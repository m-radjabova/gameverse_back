from database import get_connection
from schema.debtor import Debt, Debtor, RequestPayment

class DebtorService:

    def get_debtors(self, shop_id: int, name: str = None, page: int = 1, limit: int = 5):
        connect = get_connection()
        cursor = connect.cursor()
        try:
            page = max(1, page)  
            limit = max(1, min(limit, 100))  
            offset = (page - 1) * limit

            conditions = ["d.shop_id = %s"]
            filter_values = [shop_id]

            if name:
                conditions.append("d.full_name ILIKE %s")
                filter_values.append(f"%{name}%")

            where_clause = " WHERE " + " AND ".join(conditions)

            count_query = "SELECT COUNT(*) AS count FROM debtor d" + where_clause
            cursor.execute(count_query, filter_values)
            total = cursor.fetchone()['count']

            data_query = """
                SELECT 
                    d.debtor_id, 
                    d.full_name, 
                    d.phone_number,
                    COALESCE(SUM(
                        CASE 
                            WHEN db.status = false THEN db.amount 
                            ELSE 0 
                        END
                    ), 0) AS total_debt
                FROM debtor d 
                LEFT JOIN debt db ON d.debtor_id = db.debtor_id
            """ + where_clause +  """
                GROUP BY d.debtor_id, d.full_name, d.phone_number
                LIMIT %s OFFSET %s
            """

            data_values = filter_values + [limit, offset]
            cursor.execute(data_query, data_values)
            debtors = cursor.fetchall()

            return {
                "data": debtors,
                "total": total,
                "page": page,
                "limit": limit,
            }

        finally:
            cursor.close()
            connect.close()

    def get_debtor_by_id(self, debtor_id: int, shop_id: int):
        connect = get_connection()
        cursor = connect.cursor()
        try:
            cursor.execute(
                """
                SELECT 
                    d.debtor_id,
                    d.full_name,
                    d.phone_number,
                    d.shop_id,
                    COALESCE(SUM(db.amount), 0) AS total_debt
                FROM debtor d
                LEFT JOIN debt db ON d.debtor_id = db.debtor_id
                WHERE d.debtor_id = %s AND d.shop_id = %s
                GROUP BY d.debtor_id
                """,
                (debtor_id, shop_id),
            )
            debtor = cursor.fetchone()
            return debtor
        finally:
            cursor.close()
            connect.close()

    def create_debtor(self, shop_id: int, debtor: Debtor):
        connect = get_connection()
        cursor = connect.cursor()
        try:
            cursor.execute(
                "INSERT INTO debtor (shop_id, full_name, phone_number) VALUES (%s, %s, %s) RETURNING debtor_id",
                (shop_id, debtor.full_name, debtor.phone_number),
            )
            debtor_id = cursor.fetchone()["debtor_id"]
            connect.commit()
            return debtor_id
        finally:
            cursor.close()
            connect.close()

    def add_debt_to_debtor(self, debtor_id: int, shop_id: int, debt: Debt):
        connect = get_connection()
        cursor = connect.cursor()
        try:
            cursor.execute(
                "SELECT debtor_id FROM debtor WHERE debtor_id = %s AND shop_id = %s",
                (debtor_id, shop_id)
            )
            if not cursor.fetchone():
                return {"success": False, "message": "Debtor not found in this shop"}
            
            cursor.execute(
                """
                INSERT INTO debt (debtor_id, amount, status)
                VALUES (%s, %s, %s)
                RETURNING debt_id
                """,
                (debtor_id, debt.amount, debt.status),
            )
            debt_id = cursor.fetchone()["debt_id"]
            connect.commit()
            return {"success": True, "debt_id": debt_id}
        except Exception as e:
            connect.rollback()
            return {"success": False, "message": str(e)}
        finally:
            cursor.close()
            connect.close()

    def get_debt_by_debtor_id(self, debtor_id: int, shop_id: int):
        connect = get_connection()
        cursor = connect.cursor()
        try:
            cursor.execute(
                """
                SELECT 
                    db.debt_id,
                    db.date_time,
                    db.amount,
                    db.status,
                    GREATEST(
                        db.amount - COALESCE(SUM(p.amount), 0),
                        0
                    ) AS remaining
                FROM debt db
                INNER JOIN debtor d ON db.debtor_id = d.debtor_id
                LEFT JOIN payment_history p ON db.debt_id = p.debt_id
                WHERE db.debtor_id = %s AND d.shop_id = %s
                GROUP BY db.debt_id
                ORDER BY db.date_time ASC
                """,
                (debtor_id, shop_id),
            )
            return cursor.fetchall()
        finally:
            cursor.close()
            connect.close()

    def get_payments_by_debt_id(self, debt_id: int):
        connect = get_connection()
        cursor = connect.cursor()
        try:
            cursor.execute(
                """
                SELECT 
                    COALESCE(SUM(amount), 0) AS summa
                FROM payment_history
                WHERE debt_id = %s
                """,
                (debt_id,),
            )
            result = cursor.fetchone()
            return result["summa"]
        finally:
            cursor.close()
            connect.close()

    def get_debt_by_id(self, debt_id: int, shop_id: int = None):
        connect = get_connection()
        cursor = connect.cursor()
        try:
            if shop_id:
                cursor.execute(
                    """
                    SELECT db.debt_id, db.debtor_id, db.amount, db.status 
                    FROM debt db
                    INNER JOIN debtor d ON db.debtor_id = d.debtor_id
                    WHERE db.debt_id = %s AND d.shop_id = %s
                    """,
                    (debt_id, shop_id),
                )
            else:
                cursor.execute(
                    """
                    SELECT debt_id, debtor_id, amount, status FROM debt WHERE debt_id = %s
                    """,
                    (debt_id,),
                )
            result = cursor.fetchone()
            return result if result else None
        finally:
            cursor.close()
            connect.close()

    def repay_single_debt(self, debt_id: int, amount: int, shop_id: int = None):
        connect = get_connection()
        cursor = connect.cursor()

        try:
            debt = self.get_debt_by_id(debt_id, shop_id)
            if not debt:
                return {
                    "success": False,
                    "message": "Debt not found",
                    "paid": 0,
                    "debt_id": debt_id,
                    "status": None
                }
            
            if debt["status"] == True:
                return {
                    "success": False,
                    "message": "Debt already fully paid",
                    "paid": 0,
                    "debt_id": debt_id,
                    "status": "already_paid"
                }

            summa = self.get_payments_by_debt_id(debt_id)
            remaining_debt = debt["amount"] - summa

            if amount > remaining_debt:
                return {
                    "success": False,
                    "message": "The amount entered is greater than the amount owed.",
                    "paid": 0,
                    "debt_id": debt_id,
                    "remaining_amount": remaining_debt
                }

            if amount >= remaining_debt:
                paid_amount = remaining_debt
                cursor.execute(
                    """
                    INSERT INTO payment_history (debt_id, amount)
                    VALUES (%s, %s)
                    """,
                    (debt_id, paid_amount),
                )
                cursor.execute(
                    """
                    UPDATE debt SET status = True WHERE debt_id = %s
                    """,
                    (debt_id,),
                )
                status = "fully_paid"
            else:
                paid_amount = amount
                cursor.execute(
                    """
                    INSERT INTO payment_history (debt_id, amount)
                    VALUES (%s, %s)
                    """,
                    (debt_id, paid_amount),
                )
                status = "partially_paid"

            connect.commit()
            return {
                "success": True,
                "message": "Successfully paid debt",
                "paid": paid_amount,
                "debt_id": debt_id,
                "status": status,
                "remaining_amount": remaining_debt - paid_amount
            }

        except Exception as e:
            connect.rollback()
            return {"success": False, "message": str(e), "paid": 0, "debt_id": debt_id}
        finally:
            cursor.close()
            connect.close()

    def debt_repayment(self, debtor_id: int, amount: int, shop_id: int):
        connect = get_connection()
        cursor = connect.cursor()
        
        try:
            cursor.execute(
                """
                SELECT 
                    db.debt_id,
                    db.amount,
                    db.status,
                    COALESCE(SUM(p.amount), 0) AS paid_amount,
                    db.amount - COALESCE(SUM(p.amount), 0) AS remaining
                FROM debt db
                INNER JOIN debtor d ON db.debtor_id = d.debtor_id
                LEFT JOIN payment_history p ON db.debt_id = p.debt_id
                WHERE db.debtor_id = %s AND d.shop_id = %s AND db.status = False
                GROUP BY db.debt_id, db.amount, db.status
                ORDER BY db.date_time ASC
                """,
                (debtor_id, shop_id)
            )
            debts = cursor.fetchall()
            
            if not debts:
                return {
                    "success": False, 
                    "message": "Debts not found",
                    "remaining_amount": amount
                }
            
            remaining_amount = amount
            processed_debts = []
            
            for debt in debts:
                if remaining_amount <= 0:
                    break
                
                debt_id = debt["debt_id"]
                debt_remaining = debt["remaining"]
                
                if remaining_amount >= debt_remaining:
                    cursor.execute(
                        """
                        INSERT INTO payment_history (debt_id, amount)
                        VALUES (%s, %s)
                        """,
                        (debt_id, debt_remaining)
                    )
                    
                    cursor.execute(
                        """
                        UPDATE debt SET status = True WHERE debt_id = %s
                        """,
                        (debt_id,)
                    )
                    
                    remaining_amount -= debt_remaining
                    processed_debts.append({
                        "debt_id": debt_id,
                        "paid": debt_remaining,
                        "status": "fully_paid"
                    })
                else:
                    cursor.execute(
                        """
                        INSERT INTO payment_history (debt_id, amount)
                        VALUES (%s, %s)
                        """,
                        (debt_id, remaining_amount)
                    )
                    
                    processed_debts.append({
                        "debt_id": debt_id,
                        "paid": remaining_amount,
                        "status": "partially_paid"
                    })
                    
                    remaining_amount = 0
            
            connect.commit()
            
            return {
                "success": True,
                "message": "Payment was successful.",
                "total_paid": amount - remaining_amount,
                "remaining_amount": remaining_amount,
                "processed_debts": processed_debts
            }
            
        except Exception as e:
            connect.rollback()
            return {"success": False, "message": str(e)}
        finally:
            cursor.close()
            connect.close()

    def get_debts_history_by_debtor_id(self, debtor_id: int, shop_id: int):
        connect = get_connection()
        cursor = connect.cursor()

        try:
            cursor.execute(
                """
                SELECT db.debt_id, db.amount, db.status, db.date_time
                FROM debt db
                INNER JOIN debtor d ON db.debtor_id = d.debtor_id
                WHERE db.debtor_id = %s AND d.shop_id = %s
                ORDER BY db.date_time DESC
                """,
                (debtor_id, shop_id),
            )
            debts = cursor.fetchall()

            result = []

            for debt in debts: 
                payments = self.get_payment_history_by_debt_id(debt["debt_id"])

                total_paid = sum(p["amount"] for p in payments)
                remaining = debt["amount"] - total_paid

                result.append({
                    "debt_id": debt["debt_id"],
                    "date_time": debt["date_time"],
                    "amount": debt["amount"],
                    "status": debt["status"],
                    "total_paid": total_paid,
                    "remaining": remaining,
                    "payments": payments,
                })

            return result

        finally:
            cursor.close()
            connect.close()

    def get_payment_history_by_debt_id(self, debt_id: int):
        connect = get_connection()
        cursor = connect.cursor()
        try:
            cursor.execute(
                """
                SELECT 
                    payment_history_id,
                    date_time,
                    amount
                FROM payment_history
                WHERE debt_id = %s
                ORDER BY date_time DESC
                """,
                (debt_id,),
            )
            return cursor.fetchall()
        finally:
            cursor.close()
            connect.close()
    
    def get_shop_statistics(self, shop_id: int):
        connect = get_connection()
        cursor = connect.cursor()
        try:
            cursor.execute(
                """
                SELECT 
                    COUNT(DISTINCT d.debtor_id) as total_debtors,
                    COUNT(db.debt_id) as total_debts,
                    COALESCE(SUM(CASE WHEN db.status = false THEN db.amount ELSE 0 END), 0) as total_unpaid_debt,
                    COALESCE(SUM(CASE WHEN db.status = true THEN db.amount ELSE 0 END), 0) as total_paid_debt
                FROM debtor d
                LEFT JOIN debt db ON d.debtor_id = db.debtor_id
                WHERE d.shop_id = %s
                """,
                (shop_id,)
            )
            return cursor.fetchone()
        finally:
            cursor.close()
            connect.close()