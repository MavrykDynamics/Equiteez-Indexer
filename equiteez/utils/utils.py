from equiteez.models.shared import TokenType
from equiteez import models as models 

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
