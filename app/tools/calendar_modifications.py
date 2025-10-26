"""
Calendar Modification Tools - Allows agent to suggest and track transaction date changes
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# Store modifications in a JSON file (in production, this would be in a database)
MODIFICATIONS_FILE = Path(__file__).parent.parent / "data" / "calendar_modifications.json"


def _ensure_data_dir():
    """Ensure the data directory exists"""
    MODIFICATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_modifications() -> Dict[str, Any]:
    """Load current calendar modifications"""
    _ensure_data_dir()
    if MODIFICATIONS_FILE.exists():
        try:
            with open(MODIFICATIONS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {"modifications": [], "last_updated": None}
    return {"modifications": [], "last_updated": None}


def _save_modifications(data: Dict[str, Any]):
    """Save calendar modifications"""
    _ensure_data_dir()
    data["last_updated"] = datetime.now().isoformat()
    with open(MODIFICATIONS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def move_transaction(
    transaction_id: str,
    merchant_name: str,
    original_date: str,
    new_date: str,
    amount: float,
    reason: str
) -> Dict[str, Any]:
    """
    Move a transaction to a new date in the calendar.
    
    This tool records a suggestion to move a payment or transaction to optimize
    cashflow, avoid overdrafts, or improve credit utilization.
    
    **IMPORTANT:** You MUST first call get_user_transactions() to get the transaction data,
    then extract the transaction_id field from the specific transaction you want to move.
    
    Args:
        transaction_id: The transaction_id field from the transaction (REQUIRED - get this from get_user_transactions())
        merchant_name: Name of the merchant/payee (e.g., "Avalon Apartments", "Spotify")
        original_date: Original transaction date in YYYY-MM-DD format
        new_date: Proposed new date in YYYY-MM-DD format
        amount: Transaction amount
        reason: Explanation for why this move optimizes the calendar
        
    Returns:
        Confirmation of the modification with details
        
    Workflow Example:
        1. First, call get_user_transactions() to get all transactions
        2. Find the transaction you want to move (e.g., rent payment)
        3. Extract its transaction_id field (e.g., "txn_010")
        4. Then call this function:
        
        move_transaction(
            transaction_id="txn_010",  # ← From the transaction data!
            merchant_name="Avalon Apartments", 
            original_date="2023-09-15",
            new_date="2023-09-05",
            amount=1200.00,
            reason="Moving rent payment earlier to avoid overdraft risk after utilities payment"
        )
    """
    data = _load_modifications()
    
    modification = {
        "modification_id": f"mod_{len(data['modifications']) + 1}",
        "transaction_id": transaction_id,
        "merchant_name": merchant_name,
        "original_date": original_date,
        "new_date": new_date,
        "amount": amount,
        "reason": reason,
        "created_at": datetime.now().isoformat(),
        "status": "suggested"
    }
    
    # Remove any existing modification for this transaction
    data["modifications"] = [
        m for m in data["modifications"] 
        if m["transaction_id"] != transaction_id
    ]
    
    data["modifications"].append(modification)
    _save_modifications(data)
    
    return {
        "success": True,
        "modification": modification,
        "message": f"Suggested moving {merchant_name} (${amount}) from {original_date} to {new_date}"
    }


def add_planned_transaction(
    merchant_name: str,
    date: str,
    amount: float,
    category: str,
    reason: str
) -> Dict[str, Any]:
    """
    Add a new planned transaction to the calendar.
    
    This tool suggests adding a future payment or expense to the calendar
    to help with planning and cashflow management.
    
    Args:
        merchant_name: Name of the merchant/payee
        date: Planned date in YYYY-MM-DD format
        amount: Transaction amount
        category: Category (e.g., "UTILITIES", "FOOD_AND_DRINK", "TRANSFER_OUT")
        reason: Explanation for adding this planned transaction
        
    Returns:
        Confirmation of the new planned transaction
        
    Example:
        add_planned_transaction(
            "Credit Card Payment",
            "2023-09-20",
            500.00,
            "TRANSFER_OUT",
            "Plan credit card payment to keep utilization under 30%"
        )
    """
    data = _load_modifications()
    
    transaction_id = f"planned_{len([m for m in data['modifications'] if m.get('type') == 'planned']) + 1}"
    
    planned = {
        "modification_id": f"mod_{len(data['modifications']) + 1}",
        "transaction_id": transaction_id,
        "type": "planned",
        "merchant_name": merchant_name,
        "date": date,
        "amount": amount,
        "category": category,
        "reason": reason,
        "created_at": datetime.now().isoformat(),
        "status": "suggested"
    }
    
    data["modifications"].append(planned)
    _save_modifications(data)
    
    return {
        "success": True,
        "planned_transaction": planned,
        "message": f"Added planned transaction: {merchant_name} (${amount}) on {date}"
    }


def get_calendar_modifications(user_id: str = "default") -> Dict[str, Any]:
    """
    Get all current calendar modifications and planned transactions.
    
    Args:
        user_id: The user identifier
        
    Returns:
        Dictionary containing all modifications and summary statistics
        
    Example:
        modifications = get_calendar_modifications()
        # Returns: {"modifications": [...], "summary": {...}}
    """
    data = _load_modifications()
    
    # Separate moves from planned transactions
    moves = [m for m in data["modifications"] if m.get("type") != "planned"]
    planned = [m for m in data["modifications"] if m.get("type") == "planned"]
    
    # Calculate impact
    total_moved = len(moves)
    total_planned = len(planned)
    
    return {
        "modifications": data["modifications"],
        "summary": {
            "total_modifications": len(data["modifications"]),
            "transactions_moved": total_moved,
            "planned_transactions": total_planned,
            "last_updated": data.get("last_updated"),
        },
        "moves": moves,
        "planned": planned
    }


def clear_calendar_modifications(user_id: str = "default") -> Dict[str, Any]:
    """
    Clear all calendar modifications.
    
    Use this to reset the calendar to original dates or when starting fresh.
    
    Args:
        user_id: The user identifier
        
    Returns:
        Confirmation that modifications were cleared
    """
    data = {"modifications": [], "last_updated": None}
    _save_modifications(data)
    
    return {
        "success": True,
        "message": "All calendar modifications have been cleared"
    }


def approve_modification(modification_id: str) -> Dict[str, Any]:
    """
    Mark a modification as approved by the user.
    
    Args:
        modification_id: The ID of the modification to approve
        
    Returns:
        Confirmation of approval
    """
    data = _load_modifications()
    
    for mod in data["modifications"]:
        if mod["modification_id"] == modification_id:
            mod["status"] = "approved"
            mod["approved_at"] = datetime.now().isoformat()
            _save_modifications(data)
            return {
                "success": True,
                "message": f"Modification {modification_id} approved"
            }
    
    return {
        "success": False,
        "message": f"Modification {modification_id} not found"
    }

