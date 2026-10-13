from dipdup.models import Model, fields


class RwaTokenSupply(Model):
    """Issued supply in raw units, mirrored from the RWA token's total_supply big map."""

    id = fields.CharField(max_length=115, primary_key=True)
    contract = fields.CharField(max_length=36, index=True)
    token_id = fields.CharField(max_length=78)
    total_supply_raw = fields.DecimalField(max_digits=76, decimal_places=0, default=0)

    class Meta:
        table = "rwa_token_supply"
        unique_together = (("contract", "token_id"),)


class RwaTokenBalance(Model):
    """Complete ledger, including treasuries, users and orderbook escrow. Raw units."""

    id = fields.IntField(primary_key=True)
    token = fields.ForeignKeyField("models.RwaTokenSupply", related_name="balances")
    holder = fields.CharField(max_length=36)
    balance_raw = fields.DecimalField(max_digits=76, decimal_places=0)

    class Meta:
        table = "rwa_token_balance"
        unique_together = (("token", "holder"),)
