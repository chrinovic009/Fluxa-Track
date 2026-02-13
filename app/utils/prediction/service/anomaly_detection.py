from app.utils.authentication.models import Expense, Anomaly
from app.extensions import db
from sqlalchemy import func
import statistics

def detect_expense_anomaly(expense):
    amounts = [
        e.amount for e in Expense.query
        .filter_by(company_id=expense.company_id)
        .all()
    ]

    if len(amounts) < 5:
        return None

    mean = statistics.mean(amounts)
    std = statistics.stdev(amounts)

    if expense.amount > mean + 3 * std:
        anomaly = Anomaly(
            company_id=expense.company_id,
            company_user_id=expense.company_user_id,
            anomaly_type="expense",
            entity_id=expense.id,
            severity="high",
            description="Expense exceeds 3x standard deviation"
        )
        db.session.add(anomaly)
        db.session.commit()
        return anomaly

    return None
