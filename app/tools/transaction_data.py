"""
Transaction Data Tools - Provides access to user transaction data
"""
import json
from pathlib import Path
from typing import Any, Dict, List


def get_user_transactions(user_id: str = "default") -> Dict[str, Any]:
    """
    Retrieves transaction data for a user.
    
    This tool fetches the user's financial transaction history including:
    - Account balances
    - Transaction list with dates, amounts, and merchants
    - Payment categories and patterns
    
    Args:
        user_id: The user identifier (default: "default" uses sample data)
        
    Returns:
        Dictionary containing:
        - accounts: List of user's financial accounts with balances
        - added: List of transactions with dates, amounts, merchants, categories
        - Transaction summary statistics
        
    Example usage:
        To analyze a user's spending: get_user_transactions("user123")
        To use sample data: get_user_transactions()
    """
    # Load sample transaction data from examples
    data_file = Path(__file__).parent.parent / "examples" / "plaid_sample.json"
    
    try:
        with open(data_file, "r") as f:
            data = json.load(f)
        
        # Add summary statistics
        transactions = data.get("added", [])
        total_expenses = sum(
            t["amount"] for t in transactions 
            if t.get("personal_finance_category", {}).get("primary") != "INCOME"
        )
        total_income = sum(
            t["amount"] for t in transactions 
            if t.get("personal_finance_category", {}).get("primary") == "INCOME"
        )
        
        # Add helpful summary
        data["summary"] = {
            "total_transactions": len(transactions),
            "total_expenses": round(total_expenses, 2),
            "total_income": round(total_income, 2),
            "net_cashflow": round(total_income - total_expenses, 2),
            "current_balance": data["accounts"][0]["balances"]["current"] if data.get("accounts") else 0,
        }
        
        return data
        
    except FileNotFoundError:
        return {
            "error": "Transaction data not found",
            "accounts": [],
            "added": [],
            "summary": {}
        }
    except Exception as e:
        return {
            "error": f"Error loading transaction data: {str(e)}",
            "accounts": [],
            "added": [],
            "summary": {}
        }


def get_transactions_by_date_range(
    start_date: str,
    end_date: str,
    user_id: str = "default"
) -> List[Dict[str, Any]]:
    """
    Get transactions within a specific date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format (e.g., "2023-09-01")
        end_date: End date in YYYY-MM-DD format (e.g., "2023-09-30")
        user_id: The user identifier
        
    Returns:
        List of transactions within the date range
        
    Example:
        Get September transactions: get_transactions_by_date_range("2023-09-01", "2023-09-30")
    """
    data = get_user_transactions(user_id)
    transactions = data.get("added", [])
    
    filtered = [
        t for t in transactions
        if start_date <= t.get("date", "") <= end_date
    ]
    
    return filtered


def get_transactions_by_category(
    category: str,
    user_id: str = "default"
) -> List[Dict[str, Any]]:
    """
    Get all transactions for a specific spending category.
    
    Args:
        category: Category name (e.g., "FOOD_AND_DRINK", "ENTERTAINMENT", "UTILITIES", "INCOME")
        user_id: The user identifier
        
    Returns:
        List of transactions in that category with total amount
        
    Example:
        Get all food expenses: get_transactions_by_category("FOOD_AND_DRINK")
    """
    data = get_user_transactions(user_id)
    transactions = data.get("added", [])
    
    filtered = [
        t for t in transactions
        if t.get("personal_finance_category", {}).get("primary") == category
    ]
    
    total = sum(t["amount"] for t in filtered)
    
    return {
        "category": category,
        "transaction_count": len(filtered),
        "total_amount": round(total, 2),
        "transactions": filtered
    }


def get_recurring_payments(user_id: str = "default") -> List[Dict[str, Any]]:
    """
    Identifies recurring payments (subscriptions, rent, utilities).
    
    Args:
        user_id: The user identifier
        
    Returns:
        List of likely recurring payments with their patterns
        
    Example:
        Find all subscriptions: get_recurring_payments()
    """
    data = get_user_transactions(user_id)
    transactions = data.get("added", [])
    
    # Group by merchant name to find recurring patterns
    merchant_groups: Dict[str, List[Dict[str, Any]]] = {}
    for t in transactions:
        merchant = t.get("merchant_name", "Unknown")
        if merchant not in merchant_groups:
            merchant_groups[merchant] = []
        merchant_groups[merchant].append(t)
    
    # Find merchants with multiple transactions (likely recurring)
    recurring = []
    for merchant, txns in merchant_groups.items():
        if len(txns) > 1 or any(
            "subscription" in t.get("name", "").lower() or 
            "rent" in t.get("name", "").lower()
            for t in txns
        ):
            recurring.append({
                "merchant": merchant,
                "transaction_count": len(txns),
                "average_amount": round(sum(t["amount"] for t in txns) / len(txns), 2),
                "transactions": txns,
                "category": txns[0].get("personal_finance_category", {}).get("primary", "UNKNOWN")
            })
    
    return recurring

