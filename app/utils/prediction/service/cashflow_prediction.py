from datetime import date, timedelta
from sqlalchemy import func
from app.extensions import db
from app.utils.authentication.models import RevenueSource, Expense, CashFlowPrediction, PredictionModel, CompanyUser

def predict_cashflow(company_id, sale_point, company_user_id):
    today = date.today()
    start = today - timedelta(days=30)

    revenue = (
        db.session.query(func.sum(RevenueSource.amount))
        .join(CompanyUser, RevenueSource.company_user_id == CompanyUser.id)
        .filter(
            RevenueSource.company_id == company_id,
            CompanyUser.sale_point == sale_point,
            RevenueSource.created_at >= start
        )
        .scalar() or 0
    )

    expenses = (
        db.session.query(func.sum(Expense.amount))
        .join(CompanyUser, Expense.company_user_id == CompanyUser.id)
        .filter(
            Expense.company_id == company_id,
            CompanyUser.sale_point == sale_point,
            Expense.created_at >= start
        )
        .scalar() or 0
    )

    predicted_revenue = revenue / 30 * 7
    predicted_expenses = expenses / 30 * 7
    predicted_balance = predicted_revenue - predicted_expenses

    model = PredictionModel.query.filter_by(
        model_type="cashflow"
    ).first()

    prediction = CashFlowPrediction(
        company_id=company_id,
        company_user_id=company_user_id,
        period_start=today,
        period_end=today + timedelta(days=7),
        predicted_revenue=predicted_revenue,
        predicted_expenses=predicted_expenses,
        predicted_balance=predicted_balance,
        confidence_score=0.72,
        model_id=model.id if model else None
    )

    db.session.add(prediction)
    db.session.commit()

    return prediction
