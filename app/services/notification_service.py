def get_my_notifications(conn, username: str):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM notifications 
        WHERE username = %s ORDER BY created_at DESC
    """, (username,))
    rows = cursor.fetchall()
    for r in rows:
        r["created_at"] = str(r["created_at"])
    return rows

def mark_as_read(conn, username: str, notification_id: int):
    cursor = conn.cursor()
    cursor.execute("UPDATE notifications SET is_read = true WHERE notification_id = %s AND username = %s", 
                   (notification_id, username))
    conn.commit()
    return {"success": True}