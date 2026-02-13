from datetime import date, timedelta
from sqlalchemy import func
from app.extensions import db
from app.utils.authentication.models import InventoryMovement, InventoryPrediction, PredictionModel

def predict_stockout(company_id, product_id, company_user_id, current_stock):
    today = date.today()
    start = today - timedelta(days=30)

    sales = (
        db.session.query(func.sum(InventoryMovement.quantity))
        .filter(
            InventoryMovement.company_id == company_id,
            InventoryMovement.product_id == product_id,
            InventoryMovement.movement_type == "sale",
            InventoryMovement.created_at >= start
        )
        .scalar() or 0
    )

    avg_daily_sales = sales / 30 if sales > 0 else 0
    days_remaining = int(current_stock / avg_daily_sales) if avg_daily_sales else 999

    model = PredictionModel.query.filter_by(
        model_type="inventory"
    ).first()

    prediction = InventoryPrediction(
        product_id=product_id,
        company_id=company_id,
        company_user_id=company_user_id,
        predicted_stockout_date=today + timedelta(days=days_remaining),
        days_remaining=days_remaining,
        confidence_score=0.85,
        model_id=model.id if model else None
    )

    db.session.add(prediction)
    db.session.commit()

    return prediction
