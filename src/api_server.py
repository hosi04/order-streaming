from flask import Flask, request, jsonify
import mysql.connector
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 👈 Cho phép mọi origin, hoặc cấu hình cụ thể hơn nếu muốn


# Connect to MySQL
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="123",
    database="order_streaming"
)

@app.route('/api/orders', methods=['POST'])
def save_order():
    try:
        data = request.get_json()
        cursor = db.cursor()

        # Tạo đơn hàng (chỉ cần tạo dòng rỗng để lấy order_id)
        cursor.execute("INSERT INTO orders () VALUES ()")
        order_id = cursor.lastrowid  # Lấy id đơn hàng vừa tạo

        for item in data['cart']:
            cursor.execute(
                "INSERT INTO order_items (order_id, name, brand, price, quantity) VALUES (%s, %s, %s, %s, %s)",
                (order_id, item['name'], item['brand'], item['price'], item['quantity'])
            )

        db.commit()
        return jsonify({'message': 'Đơn hàng đã được lưu', 'order_id': order_id}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
