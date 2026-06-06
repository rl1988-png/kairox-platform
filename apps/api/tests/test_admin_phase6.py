from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from kairox_api.constants.enums import (
    AuditAction,
    ErrorCode,
    RechargeStatus,
    TxVerifyVerdict,
    UserRole,
    WithdrawStatus,
)
from kairox_api.core.errors import AppError
from kairox_api.services.admin_service import AdminService
from kairox_api.services.support_verify_service import SupportVerifyService
from kairox_api.services.withdraw_service import WithdrawService


def _user(role: UserRole = UserRole.ADMIN) -> object:
    return type("User", (), {"id": uuid4(), "role": role, "vip_level": 1})()


class FakeUserRepo:
    def __init__(self, user: object | None = None) -> None:
        self._user = user

    async def get_by_id(self, user_id: UUID) -> object | None:
        if self._user is None:
            return None
        return self._user

    async def count_all(self) -> int:
        return 1

    async def count_active_today(self) -> int:
        return 1

    async def search(self, search: str = "", page: int = 1, limit: int = 20):
        return ([], 0)


class FakeLedgerRepo:
    def __init__(self, available: Decimal = Decimal("1000")) -> None:
        self.available = available
        self.locked = Decimal("0")
        self.credits: list[Decimal] = []
        self.debits: list[Decimal] = []
        self.locks: list[Decimal] = []
        self.unlocks: list[Decimal] = []

    async def get_balance(self, user_id: UUID) -> object:
        return type("Bal", (), {"available": self.available, "locked": self.locked})()

    async def credit(self, user_id, amount, entry_type, reference_id=None, reference_type=None):
        self.available += amount
        self.credits.append(amount)
        return object()

    async def debit(self, user_id, amount, entry_type, reference_id=None, reference_type=None):
        self.available -= amount
        self.debits.append(amount)
        return object()

    async def lock(self, user_id, amount, entry_type, reference_id=None, reference_type=None):
        self.available -= amount
        self.locked += amount
        self.locks.append(amount)
        return object()

    async def unlock(self, user_id, amount, entry_type, reference_id=None, reference_type=None):
        self.locked -= amount
        self.available += amount
        self.unlocks.append(amount)
        return object()


class FakeAuditRepo:
    def __init__(self) -> None:
        self.entries: list[dict[str, object]] = []
        self._idempotency: dict[str, object] = {}

    async def log(self, **kwargs: object) -> object:
        entry = type("Audit", (), {"id": uuid4(), **kwargs})()
        self.entries.append(kwargs)
        return entry

    async def list_entries(self, *args, **kwargs):
        return [], 0

    async def get_idempotency(self, key: str) -> object | None:
        return self._idempotency.get(key)

    async def save_idempotency(self, key, admin_user_id, target_user_id, audit_log_id):
        record = type(
            "Idem",
            (),
            {
                "target_user_id": target_user_id,
                "idempotency_key": key,
            },
        )()
        self._idempotency[key] = record
        return record


class FakeRechargeRepo:
    async def count_pending(self) -> int:
        return 0

    async def sum_paid_today(self) -> Decimal:
        return Decimal("0")

    async def get_by_tx_hash(self, tx_hash: str):
        return None

    async def list_pending_active(self, limit: int = 200):
        return []


class FakeTradeRepo:
    async def count_today(self) -> int:
        return 0

    async def list_recent(self, limit: int = 50):
        return []


class FakeWithdrawRepo:
    def __init__(self) -> None:
        self.request = type(
            "Withdraw",
            (),
            {
                "id": uuid4(),
                "user_id": uuid4(),
                "amount": Decimal("50"),
                "fee_amount": Decimal("1"),
                "to_address": "T" + "x" * 33,
                "status": WithdrawStatus.PENDING,
                "admin_note": None,
                "tx_hash": None,
                "confirmations": 0,
                "broadcasted_at": None,
                "confirmed_at": None,
                "failed_at": None,
            },
        )()

    async def create(self, user_id, amount, fee_amount, to_address):
        return self.request

    async def get_by_id(self, request_id: UUID):
        return self.request

    async def get_pending_for_user(self, user_id: UUID):
        return None

    async def list_for_user(self, user_id: UUID):
        return []

    async def list_by_status(self, status=None, limit: int = 50):
        return []

    async def list_pending(self):
        return []

    async def save(self, request):
        return request

    async def sum_pending_amount(self) -> Decimal:
        return Decimal("0")

    async def count_pending(self) -> int:
        return 0


def _admin_service(
    user_repo: FakeUserRepo | None = None,
    ledger: FakeLedgerRepo | None = None,
    audit: FakeAuditRepo | None = None,
) -> AdminService:
    target = type(
        "User",
        (),
        {"id": uuid4(), "role": UserRole.USER, "vip_level": 1},
    )()
    user_repo = user_repo or FakeUserRepo(target)
    ledger = ledger or FakeLedgerRepo()
    audit = audit or FakeAuditRepo()
    withdraw_repo = FakeWithdrawRepo()
    withdraw_service = WithdrawService(withdraw_repo, ledger)  # type: ignore[arg-type]
    return AdminService(
        user_repo,  # type: ignore[arg-type]
        ledger,  # type: ignore[arg-type]
        audit,  # type: ignore[arg-type]
        FakeRechargeRepo(),  # type: ignore[arg-type]
        FakeTradeRepo(),  # type: ignore[arg-type]
        withdraw_repo,  # type: ignore[arg-type]
        withdraw_service,
    )


@pytest.mark.asyncio
async def test_manual_credit_without_admin_role() -> None:
    service = _admin_service()
    support = _user(UserRole.SUPPORT)
    with pytest.raises(AppError) as exc:
        await service.manual_credit(
            support,  # type: ignore[arg-type]
            uuid4(),
            "100",
            "Support compensation #1234",
            "key-1",
        )
    assert exc.value.code == ErrorCode.FORBIDDEN


@pytest.mark.asyncio
async def test_manual_credit_idempotent_no_double_ledger() -> None:
    audit = FakeAuditRepo()
    ledger = FakeLedgerRepo()
    service = _admin_service(audit=audit, ledger=ledger)
    admin = _user(UserRole.ADMIN)
    target_id = uuid4()
    target = type("User", (), {"id": target_id, "role": UserRole.USER, "vip_level": 1})()
    service._user_repo = FakeUserRepo(target)  # type: ignore[attr-defined]

    await service.manual_credit(
        admin,  # type: ignore[arg-type]
        target_id,
        "100",
        "Support compensation #1234",
        "idem-key-1",
    )
    assert len(ledger.credits) == 1

    result = await service.manual_credit(
        admin,  # type: ignore[arg-type]
        target_id,
        "100",
        "Support compensation #1234",
        "idem-key-1",
    )
    assert result["idempotent"] is True
    assert len(ledger.credits) == 1


@pytest.mark.asyncio
async def test_withdraw_request_over_balance() -> None:
    ledger = FakeLedgerRepo(available=Decimal("5"))
    withdraw_repo = FakeWithdrawRepo()
    service = WithdrawService(withdraw_repo, ledger)  # type: ignore[arg-type]
    user = type(
        "User",
        (),
        {
            "id": uuid4(),
            "is_official": True,
            "withdrawal_address": "T" + "a" * 33,
        },
    )()
    with pytest.raises(AppError) as exc:
        await service.create_request(user, Decimal("50"))  # type: ignore[arg-type]
    assert exc.value.code == ErrorCode.INSUFFICIENT_FUNDS


@pytest.mark.asyncio
async def test_withdraw_approve_moves_to_processing_without_debit() -> None:
    ledger = FakeLedgerRepo(available=Decimal("100"))
    audit = FakeAuditRepo()
    withdraw_repo = FakeWithdrawRepo()
    withdraw_service = WithdrawService(withdraw_repo, ledger)  # type: ignore[arg-type]
    service = AdminService(
        FakeUserRepo(),  # type: ignore[arg-type]
        ledger,  # type: ignore[arg-type]
        audit,  # type: ignore[arg-type]
        FakeRechargeRepo(),  # type: ignore[arg-type]
        FakeTradeRepo(),  # type: ignore[arg-type]
        withdraw_repo,  # type: ignore[arg-type]
        withdraw_service,
    )
    admin = _user(UserRole.ADMIN)
    await service.approve_withdraw(admin, withdraw_repo.request.id, "TX sent", "hash123456789")  # type: ignore[arg-type]
    assert len(ledger.unlocks) == 0
    assert len(ledger.debits) == 0
    assert withdraw_repo.request.status == WithdrawStatus.PROCESSING
    assert withdraw_repo.request.tx_hash == "hash123456789"
    assert len(audit.entries) == 1
    assert audit.entries[0]["action"] == AuditAction.WITHDRAW_APPROVE


@pytest.mark.asyncio
async def test_withdraw_confirm_debits_and_audits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("kairox_api.services.withdraw_service.settings.tron_min_confirmations", 2)
    ledger = FakeLedgerRepo(available=Decimal("100"))
    audit = FakeAuditRepo()
    withdraw_repo = FakeWithdrawRepo()
    withdraw_repo.request.status = WithdrawStatus.PROCESSING
    withdraw_repo.request.tx_hash = "hash123456789"
    withdraw_service = WithdrawService(withdraw_repo, ledger)  # type: ignore[arg-type]
    service = AdminService(
        FakeUserRepo(),  # type: ignore[arg-type]
        ledger,  # type: ignore[arg-type]
        audit,  # type: ignore[arg-type]
        FakeRechargeRepo(),  # type: ignore[arg-type]
        FakeTradeRepo(),  # type: ignore[arg-type]
        withdraw_repo,  # type: ignore[arg-type]
        withdraw_service,
    )
    admin = _user(UserRole.ADMIN)
    await service.confirm_withdraw(admin, withdraw_repo.request.id, 2, "Confirmed")  # type: ignore[arg-type]
    assert len(ledger.unlocks) == 1
    assert len(ledger.debits) == 1
    assert withdraw_repo.request.status == WithdrawStatus.COMPLETED
    assert withdraw_repo.request.confirmations == 2
    assert len(audit.entries) == 1
    assert audit.entries[0]["action"] == AuditAction.WITHDRAW_CONFIRM


@pytest.mark.asyncio
async def test_withdraw_confirm_requires_min_confirmations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("kairox_api.services.withdraw_service.settings.tron_min_confirmations", 19)
    withdraw_repo = FakeWithdrawRepo()
    withdraw_repo.request.status = WithdrawStatus.PROCESSING
    withdraw_repo.request.tx_hash = "hash123456789"
    service = WithdrawService(withdraw_repo, FakeLedgerRepo())  # type: ignore[arg-type]
    with pytest.raises(AppError) as exc:
        await service.confirm(withdraw_repo.request.id, 3)
    assert exc.value.code == ErrorCode.VALIDATION_ERROR


@pytest.mark.asyncio
async def test_withdraw_fail_unlocks_processing_request() -> None:
    ledger = FakeLedgerRepo(available=Decimal("100"))
    withdraw_repo = FakeWithdrawRepo()
    withdraw_repo.request.status = WithdrawStatus.PROCESSING
    withdraw_repo.request.tx_hash = "hash123456789"
    service = WithdrawService(withdraw_repo, ledger)  # type: ignore[arg-type]
    await service.fail(withdraw_repo.request.id, "Broadcast failed")
    assert len(ledger.unlocks) == 1
    assert len(ledger.debits) == 0
    assert withdraw_repo.request.status == WithdrawStatus.FAILED


@pytest.mark.asyncio
async def test_withdraw_reject_unlocks_no_debit() -> None:
    ledger = FakeLedgerRepo(available=Decimal("100"))
    audit = FakeAuditRepo()
    withdraw_repo = FakeWithdrawRepo()
    withdraw_service = WithdrawService(withdraw_repo, ledger)  # type: ignore[arg-type]
    service = AdminService(
        FakeUserRepo(),  # type: ignore[arg-type]
        ledger,  # type: ignore[arg-type]
        audit,  # type: ignore[arg-type]
        FakeRechargeRepo(),  # type: ignore[arg-type]
        FakeTradeRepo(),  # type: ignore[arg-type]
        withdraw_repo,  # type: ignore[arg-type]
        withdraw_service,
    )
    admin = _user(UserRole.ADMIN)
    await service.reject_withdraw(admin, withdraw_repo.request.id, "Invalid address")  # type: ignore[arg-type]
    assert len(ledger.unlocks) == 1
    assert len(ledger.debits) == 0
    assert withdraw_repo.request.status == WithdrawStatus.REJECTED
    assert ledger.unlocks[0] == Decimal("51")


class FakeTron:
    def __init__(self, transfer: object | None = None) -> None:
        self._transfer = transfer

    async def fetch_transfer_by_hash(self, tx_hash: str, contract: str):
        return self._transfer

    @staticmethod
    def address_matches(actual: str, expected: str) -> bool:
        return actual == expected


@pytest.mark.asyncio
async def test_tx_verify_already_used() -> None:
    existing = type(
        "Order",
        (),
        {
            "id": uuid4(),
            "amount": Decimal("30"),
            "deposit_address": "Tdeposit",
            "status": RechargeStatus.PAID,
        },
    )()

    class Repo(FakeRechargeRepo):
        async def get_by_tx_hash(self, tx_hash: str):
            return existing

    service = SupportVerifyService(Repo(), FakeTron())  # type: ignore[arg-type]
    result = await service.verify_recharge_tx("hash-used")
    assert result["verdict"] == TxVerifyVerdict.ALREADY_USED.value


@pytest.mark.asyncio
async def test_tx_verify_amount_mismatch(monkeypatch: pytest.MonkeyPatch) -> None:
    deposit = "T" + "a" * 33
    monkeypatch.setattr(
        "kairox_api.services.support_verify_service.settings.tron_deposit_address",
        deposit,
    )
    transfer = type(
        "Transfer",
        (),
        {
            "amount": Decimal("30"),
            "to_address": deposit,
            "confirmations": 20,
        },
    )()

    class Repo(FakeRechargeRepo):
        async def list_pending_active(self, limit: int = 200):
            return [
                type(
                    "Order",
                    (),
                    {
                        "id": uuid4(),
                        "expected_amount": Decimal("50"),
                        "deposit_address": deposit,
                    },
                )()
            ]

    service = SupportVerifyService(Repo(), FakeTron(transfer))  # type: ignore[arg-type]
    result = await service.verify_recharge_tx("hash-mismatch")
    assert result["verdict"] == TxVerifyVerdict.AMOUNT_MISMATCH.value


@pytest.mark.asyncio
async def test_admin_mutation_creates_single_audit_row() -> None:
    audit = FakeAuditRepo()
    service = _admin_service(audit=audit)
    admin = _user(UserRole.ADMIN)
    target_id = uuid4()
    target = type("User", (), {"id": target_id, "role": UserRole.USER, "vip_level": 2})()
    service._user_repo = FakeUserRepo(target)  # type: ignore[attr-defined]

    await service.adjust_vip(
        admin,  # type: ignore[arg-type]
        target_id,
        3,
        "Manual VIP upgrade approved",
    )
    assert len(audit.entries) == 1
    assert audit.entries[0]["action"] == AuditAction.VIP_LEVEL_ADJUST


@pytest.mark.asyncio
async def test_withdraw_bind_address_success() -> None:
    user = type(
        "User",
        (),
        {"id": uuid4(), "withdrawal_address": None, "withdrawal_network": None},
    )()
    service = WithdrawService(FakeWithdrawRepo(), FakeLedgerRepo())  # type: ignore[arg-type]
    updated = await service.bind_address(user, "TRC20", "T" + "b" * 33)  # type: ignore[arg-type]
    assert updated.withdrawal_address is not None


@pytest.mark.asyncio
async def test_withdraw_bind_address_already_bound() -> None:
    user = type(
        "User",
        (),
        {"id": uuid4(), "withdrawal_address": "T" + "x" * 33, "withdrawal_network": "TRC20"},
    )()
    service = WithdrawService(FakeWithdrawRepo(), FakeLedgerRepo())  # type: ignore[arg-type]
    with pytest.raises(AppError) as exc:
        await service.bind_address(user, "TRC20", "T" + "b" * 33)  # type: ignore[arg-type]
    assert exc.value.code == ErrorCode.CONFLICT


@pytest.mark.asyncio
async def test_withdraw_trial_blocked(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "kairox_api.services.withdraw_service.settings.block_trial_withdraw",
        True,
    )
    user = type(
        "User",
        (),
        {"id": uuid4(), "is_official": False, "withdrawal_address": "T" + "a" * 33},
    )()
    service = WithdrawService(FakeWithdrawRepo(), FakeLedgerRepo())  # type: ignore[arg-type]
    with pytest.raises(AppError) as exc:
        await service.create_request(user, Decimal("50"))  # type: ignore[arg-type]
    assert exc.value.code == ErrorCode.FORBIDDEN


@pytest.mark.asyncio
async def test_withdraw_pending_conflict() -> None:
    class Repo(FakeWithdrawRepo):
        async def get_pending_for_user(self, user_id):
            return object()

    service = WithdrawService(Repo(), FakeLedgerRepo())  # type: ignore[arg-type]
    user = type(
        "User",
        (),
        {"id": uuid4(), "is_official": True, "withdrawal_address": "T" + "a" * 33},
    )()
    with pytest.raises(AppError) as exc:
        await service.create_request(user, Decimal("50"))  # type: ignore[arg-type]
    assert exc.value.code == ErrorCode.CONFLICT


@pytest.mark.asyncio
async def test_withdraw_approve_not_found() -> None:
    class EmptyRepo(FakeWithdrawRepo):
        async def get_by_id(self, request_id: UUID):
            return None

    service = WithdrawService(EmptyRepo(), FakeLedgerRepo())  # type: ignore[arg-type]
    with pytest.raises(AppError) as exc:
        await service.approve(uuid4())
    assert exc.value.code == ErrorCode.NOT_FOUND


@pytest.mark.asyncio
async def test_withdraw_create_request_success() -> None:
    ledger = FakeLedgerRepo()
    service = WithdrawService(FakeWithdrawRepo(), ledger)  # type: ignore[arg-type]
    user = type(
        "User",
        (),
        {"id": uuid4(), "is_official": True, "withdrawal_address": "T" + "a" * 33},
    )()
    req = await service.create_request(user, Decimal("20"))  # type: ignore[arg-type]
    assert req is not None
    assert ledger.locked == Decimal("21")
    assert ledger.locks[0] == Decimal("21")


@pytest.mark.asyncio
async def test_withdraw_bind_wrong_network() -> None:
    user = type("User", (), {"id": uuid4(), "withdrawal_address": None})()
    service = WithdrawService(FakeWithdrawRepo(), FakeLedgerRepo())  # type: ignore[arg-type]
    with pytest.raises(AppError) as exc:
        await service.bind_address(user, "ERC20", "T" + "b" * 33)  # type: ignore[arg-type]
    assert exc.value.code == ErrorCode.VALIDATION_ERROR


@pytest.mark.asyncio
async def test_admin_get_user_not_found() -> None:
    service = _admin_service(user_repo=FakeUserRepo(None))
    with pytest.raises(AppError) as exc:
        await service.get_user(uuid4())
    assert exc.value.code == ErrorCode.NOT_FOUND


@pytest.mark.asyncio
async def test_admin_manual_credit_invalid_amount() -> None:
    service = _admin_service()
    admin = _user(UserRole.ADMIN)
    target = type("User", (), {"id": uuid4(), "role": UserRole.USER, "vip_level": 1})()
    service._user_repo = FakeUserRepo(target)  # type: ignore[attr-defined]
    with pytest.raises(AppError) as exc:
        await service.manual_credit(
            admin,  # type: ignore[arg-type]
            target.id,  # type: ignore[attr-defined]
            "bad",
            "Valid reason here",
            "key-x",
        )
    assert exc.value.code == ErrorCode.VALIDATION_ERROR


@pytest.mark.asyncio
async def test_admin_dashboard_returns_metrics() -> None:
    service = _admin_service()
    data = await service.get_dashboard()
    assert "users_total" in data
    assert "hot_wallet_balance" in data


@pytest.mark.asyncio
async def test_tx_verify_credit_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    deposit = "T" + "c" * 33
    monkeypatch.setattr(
        "kairox_api.services.support_verify_service.settings.tron_deposit_address",
        deposit,
    )
    transfer = type(
        "Transfer",
        (),
        {"amount": Decimal("30"), "to_address": deposit, "confirmations": 20},
    )()
    order_id = uuid4()

    class Repo(FakeRechargeRepo):
        async def list_pending_active(self, limit: int = 200):
            return [
                type(
                    "Order",
                    (),
                    {
                        "id": order_id,
                        "expected_amount": Decimal("30"),
                        "deposit_address": deposit,
                    },
                )()
            ]

    service = SupportVerifyService(Repo(), FakeTron(transfer))  # type: ignore[arg-type]
    result = await service.verify_recharge_tx("hash-ok")
    assert result["verdict"] == TxVerifyVerdict.CREDIT_OK.value
    assert result["matched_order_id"] == str(order_id)
