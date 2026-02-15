from datetime import date, timedelta
from sqlalchemy import func
from app.extensions import db
from app.utils.authentication.models import InventoryMovement, SalesPrediction, PredictionModel, CompanyUser, Product
from app.utils.prediction.utils.statistics import safe_mean, safe_std

def predict_sales(company_id, product_id, sale_point, company_user_id):
    today = date.today()
    start = today - timedelta(days=30)

    # Historique des ventes quotidiennes
    history = (
        db.session.query(
            func.date(InventoryMovement.created_at).label("day"),
            func.sum(InventoryMovement.quantity).label("qty")
        )
        .join(CompanyUser, CompanyUser.id == InventoryMovement.company_user_id)
        .filter(
            InventoryMovement.company_id == company_id,
            InventoryMovement.product_id == product_id,
            InventoryMovement.movement_type == "sale",
            CompanyUser.sale_point == sale_point,
            InventoryMovement.created_at >= start
        )
        .group_by(func.date(InventoryMovement.created_at))
        .all()
    )

    daily_sales = [row.qty for row in history if row.qty]

    # Moyenne et volatilité
    avg_daily_sales = safe_mean(daily_sales)
    std_daily_sales = safe_std(daily_sales)

    # Prédiction : moyenne ± volatilité
    predicted_quantity = avg_daily_sales * 7
    lower_bound = max(0, (avg_daily_sales - std_daily_sales) * 7)
    upper_bound = (avg_daily_sales + std_daily_sales) * 7

    # Calcul du revenu prédit
    product = Product.query.get(product_id)
    predicted_revenue = float(predicted_quantity) * float(product.unit_price)

    # Score de confiance basé sur la volatilité
    confidence_score = max(0.5, 1 - (std_daily_sales / avg_daily_sales)) if avg_daily_sales > 0 else 0.5

    model = PredictionModel.query.filter_by(model_type="sales").first()

    prediction = SalesPrediction(
        company_id=company_id,
        product_id=product_id,
        company_user_id=company_user_id,
        period_start=today,
        period_end=today + timedelta(days=7),
        predicted_quantity=predicted_quantity,
        predicted_revenue=predicted_revenue,
        confidence_score=confidence_score,
        model_id=model.id if model else None
    )

    db.session.add(prediction)
    db.session.commit()

    return {
        "sale_point": sale_point,
        "product": product.name,
        "predicted_quantity": int(predicted_quantity),
        "predicted_revenue": round(predicted_revenue, 2),
        "confidence": f"{confidence_score*100:.0f}%",
        "period": f"{today.strftime('%d %b %Y')} → {(today + timedelta(days=7)).strftime('%d %b %Y')}",
        "range": f"{int(lower_bound)} - {int(upper_bound)} unités"
    }
