from dipdup.context import HandlerContext
from dipdup.models.tezos import TezosTransaction
from equiteez import models as models
from equiteez.types.super_admin.tezos_parameters.sign_action import SignActionParameter
from equiteez.types.super_admin.tezos_storage import SuperAdminStorage
from equiteez.utils.utils import create_super_admin_action, get_contract_metadata
from dateutil import parser


async def sign_action(
    ctx: HandlerContext,
    sign_action: TezosTransaction[SignActionParameter, SuperAdminStorage],
) -> None:
    # Fetch operations info
    address = sign_action.data.target_address
    signatory_action_ledger = sign_action.storage.signatoryActionLedger
    signatory_ledger = sign_action.storage.signatoryLedger
    user_role_ledger = sign_action.storage.userRoleLedger
    lambda_ledger = sign_action.storage.lambdaLedger
    signatory_size = sign_action.storage.signatorySize
    baker = sign_action.storage.baker
    diffs = sign_action.data.diffs

    # Make sure all touched actions exist locally and
    # save signatures from the action signers
    await create_super_admin_action(sign_action)

    # Get super admin
    super_admin = await models.SuperAdmin.get(address=address)
    super_admin.signatory_size = signatory_size
    super_admin.baker = baker
    await super_admin.save()

    # Update action records
    for action_id in signatory_action_ledger:
        # Fetch action params
        action_record = signatory_action_ledger[action_id]
        executed = action_record.executed
        if action_record.status == "EXECUTED":
            status = models.ActionStatus.EXECUTED
        elif action_record.status == "FLUSHED":
            status = models.ActionStatus.FLUSHED
        else:
            status = models.ActionStatus.PENDING
        signers_count = action_record.signersCount
        executed_level = action_record.executedLevel

        # Save action
        action = await models.SuperAdminSignatoryAction.get(
            super_admin=super_admin, action_id=action_id
        )
        action.executed = executed
        action.status = status
        action.signers_count = signers_count
        if action_record.executedDateTime:
            action.executed_datetime = parser.parse(action_record.executedDateTime)
        action.executed_level = executed_level
        await action.save()

    # Update config
    threshold = sign_action.storage.config.threshold
    action_expiry_in_seconds = sign_action.storage.config.actionExpiryInSeconds
    super_admin.threshold = threshold
    super_admin.action_expiry_in_seconds = action_expiry_in_seconds
    await super_admin.save()

    # Refresh metadata when an executed updateMetadata action wrote to the
    # super admin's own metadata big map (the storage field only carries the
    # diffs of this operation, so it is empty otherwise)
    if sign_action.storage.metadata:
        super_admin.metadata = await get_contract_metadata(ctx=ctx, address=address)
        await super_admin.save()

    # User roles
    for user_role_record in user_role_ledger:
        # Fetch params
        role_user_address = user_role_record.key.address_0
        role = user_role_record.key.string
        contract_address = user_role_record.key.address_1

        # Save user role
        user, _ = await models.EquiteezUser.get_or_create(address=role_user_address)
        await user.save()
        user_role, _ = await models.SuperAdminUserRole.get_or_create(
            super_admin=super_admin,
            user=user,
            role=role,
            contract_address=contract_address,
        )
        await user_role.save()

    # Add signatory
    for signatory_address in signatory_ledger:
        user, _ = await models.EquiteezUser.get_or_create(address=signatory_address)
        await user.save()
        await models.SuperAdminSignatory.get_or_create(
            super_admin=super_admin, user=user
        )

    # Save lambdas applied by executed actions
    for lambda_name in lambda_ledger:
        contract_lambda, _ = await models.SuperAdminLambda.get_or_create(
            contract=super_admin,
            lambda_name=lambda_name,
        )
        contract_lambda.lambda_bytes = lambda_ledger[lambda_name]
        await contract_lambda.save()

    # Diff based removals
    for diff in diffs:
        # Fetch params
        path = diff["path"]
        diff_action = diff["action"]
        content = diff["content"]

        if diff_action == "remove_key":
            # Remove signatory
            if path == "signatoryLedger":
                signatory_address = content["key"]
                user, _ = await models.EquiteezUser.get_or_create(
                    address=signatory_address
                )
                await user.save()
                await models.SuperAdminSignatory.filter(
                    super_admin=super_admin, user=user
                ).delete()

            # Remove user role
            if path == "userRoleLedger":
                user_role_key = content["key"]
                role_user_address = user_role_key["address_0"]
                role = user_role_key["string"]
                contract_address = user_role_key["address_1"]
                user, _ = await models.EquiteezUser.get_or_create(
                    address=role_user_address
                )
                await user.save()
                await models.SuperAdminUserRole.filter(
                    super_admin=super_admin,
                    user=user,
                    role=role,
                    contract_address=contract_address,
                ).delete()
