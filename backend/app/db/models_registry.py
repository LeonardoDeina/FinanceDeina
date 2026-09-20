"""Import every ORM model so Base.metadata is fully populated.

Alembic's env.py and the test fixtures both need every table registered
before generating migrations or calling create_all(); importing the
modules for their side effects here keeps that in one place instead of
duplicating the list.
"""

from app.accounts import models as _accounts_models  # noqa: F401
from app.audit import models as _audit_models  # noqa: F401
from app.budgets import models as _budgets_models  # noqa: F401
from app.categories import models as _categories_models  # noqa: F401
from app.closings import models as _closings_models  # noqa: F401
from app.currency import models as _currency_models  # noqa: F401
from app.forecasting import models as _forecasting_models  # noqa: F401
from app.recurring import models as _recurring_models  # noqa: F401
from app.transactions import models as _transactions_models  # noqa: F401
from app.users import models as _users_models  # noqa: F401
