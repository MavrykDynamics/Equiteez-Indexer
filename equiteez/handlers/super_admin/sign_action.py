from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.sign_action import SignActionParameter
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from dateutil import parser

async def sign_action(
    ctx: HandlerContext,
    sign_action: TezosTransaction[SignActionParameter, SuperAdminStorage],
) -> None:
    # Fetch operations info
    address                     = sign_action.data.target_address
    signatory_action_ledger     = sign_action.storage.signatoryActionLedger
    signature_ledger            = sign_action.storage.signatureLedger
    signatory_ledger            = sign_action.storage.signatoryLedger
    general_admin_ledger        = sign_action.storage.generalAdminLedger
    contract_admin_ledger       = sign_action.storage.contractAdminLedger
    signatory_size              = sign_action.storage.signatorySize
    diffs                       = sign_action.data.diffs

    # Get super admin
    super_admin = await models.SuperAdmin.get(
        address = address
    )
    super_admin.signatory_size  = signatory_size
    await super_admin.save()

    # Save signatures
    for signature in signature_ledger:
        # Fetch params
        signatory_address   = signature.key.address
        action_id           = signature.key.nat

        # Fetch action
        action              = await models.SuperAdminSignatoryAction.get_or_none(
            super_admin = super_admin,
            action_id   = action_id
        )

        # Create a signature
        user, _             = await models.EquiteezUser.get_or_create(
            address = signatory_address
        )
        await user.save()
        signatory           = await models.SuperAdminSignatory.get(
            super_admin = super_admin,
            user        = user
        )
        signature           = models.SuperAdminSignature(
            super_admin = super_admin,
            signatory   = signatory,
            action      = action
        )
        await signature.save()

    # Update action records
    for action_id in signatory_action_ledger:
        # Fetch action params
        action_record       = signatory_action_ledger[action_id]
        executed            = action_record.executed
        status              = models.ActionStatus.EXECUTED if action_record.status == 'EXECUTED' else models.ActionStatus.FLUSHED
        signers_count       = action_record.signersCount
        executed_level      = action_record.executedLevel

        # Save action
        action              = await models.SuperAdminSignatoryAction.get(
            super_admin = super_admin,
            action_id   = action_id
        )
        action.executed            = executed
        action.status              = status
        action.signers_count       = signers_count
        if action_record.executedDateTime:
            action.executed_datetime   = parser.parse(action_record.executedDateTime)
        action.executed_level      = executed_level
        await action.save()

    # Update config
    threshold                   = sign_action.storage.config.threshold
    action_expiry_in_seconds    = sign_action.storage.config.actionExpiryInSeconds
    super_admin.threshold                   = threshold
    super_admin.action_expiry_in_seconds    = action_expiry_in_seconds
    await super_admin.save()

    # General admins
    for general_admin_address in general_admin_ledger:
        user, _             = await models.EquiteezUser.get_or_create(
            address = general_admin_address
        )
        await user.save()
        general_admin, _    = await models.SuperAdminGeneralAdmin.get_or_create(
            super_admin = super_admin,
            user        = user
        )
        await general_admin.save()

    # Contract admins
    for contract_admin_record in contract_admin_ledger:
        # Fetch params
        contract_admin_address  = contract_admin_record.key.address_0
        contract_address        = contract_admin_record.key.address_1

        # Save contract admin
        user, _             = await models.EquiteezUser.get_or_create(
            address = contract_admin_address
        )
        await user.save()
        contract_admin, _       = await models.SuperAdminContractAdmin.get_or_create(
            super_admin         = super_admin,
            user                = user,
            contract_address    = contract_address
        )
        await contract_admin.save()

    # Add signatory
    for signatory_address in signatory_ledger:
        user, _ = await models.EquiteezUser.get_or_create(
            address = signatory_address
        )
        await user.save()
        signatory   = models.SuperAdminSignatory(
            super_admin = super_admin,
            user        = user
        )
        await signatory.save()

    # Diff based removals
    for diff in diffs:
        # Fetch params
        path        = diff['path']
        diff_action = diff['action']
        content     = diff['content']

        if diff_action == "remove_key":
            # Remove signatory
            if path == "signatoryLedger":
                signatory_address   = content['key']
                user, _             = await models.EquiteezUser.get_or_create(
                    address         = signatory_address
                )
                await user.save()
                await models.SuperAdminSignatory.filter(
                    super_admin = super_admin,
                    user        = user
                ).delete()
            
            # Remove general admin
            if path == "generalAdminLedger":
                general_admin_address   = content['key']
                user, _                 = await models.EquiteezUser.get_or_create(
                    address             = general_admin_address
                )
                await user.save()
                await models.SuperAdminGeneralAdmin.filter(
                    super_admin = super_admin,
                    user        = user
                ).delete()
            
            # Remove contract admin
            if path == "contractAdminLedger":
                contract_admin_record   = content['key']
                contract_admin_address  = contract_admin_record['address_0']
                contract_address        = contract_admin_record['address_1']
                user, _                 = await models.EquiteezUser.get_or_create(
                    address             = contract_admin_address
                )
                await user.save()
                await models.SuperAdminContractAdmin.filter(
                    super_admin         = super_admin,
                    user                = user,
                    contract_address    = contract_address
                ).delete()
