from ..models.trip import TripRequest

def validate_dates(req: TripRequest) -> bool:
    # check when the payment is done
    if req.start_date >= req.end_date:
        raise ValueError("End date must be after start date")
    return True
