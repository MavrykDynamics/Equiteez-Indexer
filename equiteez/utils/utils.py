from equiteez.models.shared import TokenType
from equiteez import models as models
from dateutil import parser

# Get token contract standard
async def get_token_standard(ctx, address):
    standard                = None
    
    # MVRK case 
    if address == 'mv2ZZZZZZZZZZZZZZZZZZZZZZZZZZZDXMF2d':
        standard    = TokenType.MAV
    elif address[0:3] == 'KT1' and len(address) == 36:
        contract_summary        = None
        try:
            datasource          = ctx.get_tezos_tzkt_datasource(
                name    = 'mvkt_atlasnet'
            )
            contract_summary    = await datasource.get_contract_summary(
                address = address
            )
        except BaseException as e:
            ...
        if contract_summary:
            if 'tzips' in contract_summary:
                tzips   = contract_summary['tzips']
                if 'fa2' in tzips:
                    standard        = TokenType.FA2
                else:
                    if 'fa12' in tzips:
                        standard    = TokenType.FA12

    return standard

# Get contract metadata
async def get_contract_metadata(ctx, address):
    metadata_datasource_name    = 'metadata_atlasnet'
    metadata_datasource         = None
    contract_metadata           = None

    try:
        metadata_datasource         = ctx.get_tzip_metadata_datasource(metadata_datasource_name)
    except BaseException as e:
        ...

    if metadata_datasource:
        try:
            contract_metadata           = await metadata_datasource.get_contract_metadata(address)
        except BaseException as e:
            ...

    return contract_metadata

# Get contract token metadata
async def get_contract_token_metadata(ctx, address, token_id='0'):
    metadata_datasource_name    = 'metadata_atlasnet'
    token_metadata              = None

    try:
        metadata_datasource         = ctx.get_tzip_metadata_datasource(metadata_datasource_name)
        token_metadata              = await metadata_datasource.get_token_metadata(address, token_id)

        if not token_metadata:
            # TODO: Remove in prod
            # Check for mainnet as well
            metadata_datasource_name    = 'metadata_mainnet'
            metadata_datasource         = ctx.get_tzip_metadata_datasource(metadata_datasource_name)
            token_metadata              = await metadata_datasource.get_token_metadata(address, token_id)
    except BaseException as e:
        ...
        
    return token_metadata

# Register token
async def register_token(ctx, address):
    token, _    = await models.Token.get_or_create(
        address = address
    )
    if not token.metadata:
        token.metadata = await get_contract_metadata(
            ctx=ctx,
            address=address
        )
    if not token.token_metadata:
        token.token_metadata = await get_contract_token_metadata(
            ctx=ctx,
            address=address
        )
    if not token.token_standard:
        token.token_standard    = await get_token_standard(
            ctx=ctx,
            address=address
        )
    await token.save()
    return token

# Save contract lambda in storage
async def persist_lambda(contract_class, lambda_contract_class, set_lambda):
    
    # Get operation values
    contract_address        = set_lambda.data.target_address
    timestamp               = set_lambda.data.timestamp
    lambda_bytes            = set_lambda.parameter.func_bytes
    lambda_name             = set_lambda.parameter.name

    # Save / Update record
    contract                = await contract_class.get(
        address     = contract_address
    )
    contract.last_updated_at            = timestamp
    await contract.save()
    contract_lambda, _      = await lambda_contract_class.get_or_create(
        contract        = contract,
        lambda_name     = lambda_name,
    )
    contract_lambda.last_updated_at     = timestamp
    contract_lambda.lambda_bytes        = lambda_bytes
    await contract_lambda.save()

# Super admin actions
async def create_super_admin_action(handler):
    # Fetch operations info
    address                     = handler.data.target_address
    signatory_action_ledger     = handler.storage.signatoryActionLedger
    action_counter              = handler.storage.actionCounter

    # Get super admin
    super_admin = await models.SuperAdmin.get(
        address = address
    )
    super_admin.action_counter  = action_counter
    await super_admin.save()

    # Create action record
    for action_id in signatory_action_ledger:
        # Fetch action params
        action_record       = signatory_action_ledger[action_id]
        initiator_address   = action_record.initiator
        action_type         = action_record.actionType
        executed            = action_record.executed
        status              = models.ActionStatus.PENDING
        signers_count       = action_record.signersCount
        data_map            = action_record.dataMap
        start_datetime      = parser.parse(action_record.startDateTime)
        start_level         = action_record.startLevel
        executed_datetime   = parser.parse(action_record.executedDateTime) if action_record.executedDateTime else None
        executed_level      = action_record.executedLevel
        expiration_datetime = parser.parse(action_record.expirationDateTime)

        # Get initiator
        user, _             = await models.EquiteezUser.get_or_create(
            address = initiator_address
        )
        await user.save()
        initiator           = await models.SuperAdminSignatory.get(
            super_admin = super_admin,
            user        = user
        )

        # Create action
        action              = models.SuperAdminSignatoryAction(
            super_admin         = super_admin,
            initiator           = initiator,
            action_id           = action_id,
            action_type         = action_type,
            executed            = executed,
            status              = status,
            signers_count       = signers_count,
            start_datetime      = start_datetime,
            start_level         = start_level,
            executed_datetime   = executed_datetime,
            executed_level      = executed_level,
            expiration_datetime = expiration_datetime,
        )
        await action.save()

        # Create data records
        for data_name in data_map:
            bytes   = data_map[data_name]
            action_data = models.SuperAdminSignatoryActionData(
                action  = action,
                name    = data_name,
                bytes   = bytes
            )
            await action_data.save()
