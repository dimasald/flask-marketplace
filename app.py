from flask import Flask, render_template, request, redirect, session
import json
import sqlite3

app = Flask(__name__)

app.secret_key = "rahasia"

@app.route("/")
def home():
    if "username" in session:
        del session["username"]
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("marketplace.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        )
        user = cursor.fetchone()
        conn.close()
        if user:
            if password == user[2]:
                session["username"] = user[1]
                session["role"] = user[3]
                return redirect("/dashboard")
            else:
                return "Password salah"
        else:
            return "Username tidak ditemukan"
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("marketplace.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO users (username, password, role)
        VALUES (?, ?, ?)
        """, (username, password, "user"))
        conn.commit()
        conn.close()
        return redirect ("/login")
    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")
    else:
        conn = sqlite3.connect("marketplace.db")
        cursor = conn.cursor()
        cursor.execute (
            "SELECT username FROM users"
        )
        user = cursor.fetchall()
        cursor.execute(
            "SELECT * FROM products WHERE penjual = ?", (session["username"],)
        )
        products = cursor.fetchall()
        conn.close()
        username = session["username"]
        return render_template("dashboard.html",
                               nama_pengguna = username,
                               jumlah_user = len(user), 
                               daftar_user = user,
                               daftar_produk = products)

@app.route("/delete", methods = ["POST", "GET"])
def delete():
    if "username" not in session:
        return redirect("/login")
    else:
        if request.method == "POST":
            password = request.form["password"]
            conn = sqlite3.connect("marketplace.db")
            cursor = conn.cursor()

            cursor.execute(
                "SELECT password FROM users WHERE username = ?",
                    (session["username"],)
            )

            hasil = cursor.fetchone()
            if hasil and password == hasil[0]:
                cursor.execute(
                    "DELETE FROM users WHERE username = ?",
                    (session["username"],)
                )
                conn.commit()
                conn.close()

                session.clear()
            
                return redirect("/")
            else:
                return "The password is wrong"
        return render_template("delete.html")
    
@app.route("/change-password", methods = ["POST", "GET"])
def change_password():
    if "username" not in session:
        return redirect("/login")
    else:
        if request.method == "POST":
            password = request.form["password"]
            conn = sqlite3.connect("marketplace.db")
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password = ? WHERE username = ?",
                    (password, session["username"])
            )
            conn.commit()
            conn.close()
            return "Your account password has changed"
    return render_template("change_password.html")

@app.route("/change-name", methods = ["POST", "GET"])
def change_name():
    if "username" not in session:
        return redirect("login")
    else:
        if request.method == "POST":
            old_name = session["username"]
            name = request.form["name"]
            conn = sqlite3.connect("marketplace.db")
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET username = ? WHERE username = ?",
                    (name, old_name)
            )

            conn.commit()
            conn.close()
            
            session["username"] = name
            return redirect("/dashboard")
    return render_template("change_name.html")

@app.route("/add-product", methods = ["GET", "POST"])
def add_product():
    if "username" not in session:
        return redirect("login")
    else:
        if request.method == "POST":
            product = request.form["nama produk"]
            try:
                price = int(request.form["harga"])
            except ValueError:
                return "Harga harus berupa angka"
            description = request.form["deskripsi"]
            conn = sqlite3.connect("marketplace.db")
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO products (nama, harga, deskripsi, penjual)
            VALUES (?, ?, ?, ?)
            """, (product, price, description, session["username"]))
            conn.commit()
            conn.close()
            return redirect("/dashboard")
    return render_template("add_product.html")

@app.route("/update-product/<int:id>", methods = ["GET", "POST"])
def update_product(id):

        if request.method == "POST":
            conn = sqlite3.connect("marketplace.db")
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM products WHERE id = ?
            """, (id,)
    
            )
            products = cursor.fetchone()
            nama = products[1]
            harga = products[2]
            deskripsi = products[3]
            nama_baru = request.form["nama produk"]
            harga_baru = request.form["harga"]
            deskripsi_baru = request.form["deskripsi"]

            if nama_baru == "":
                nama_baru = nama
            if harga_baru == "":
                harga_baru = harga
            if deskripsi_baru == "":
                deskripsi_baru = deskripsi

            cursor.execute("""
            UPDATE products SET nama = ?, harga = ?, deskripsi = ? WHERE id = ? """,
               (nama_baru, harga_baru, deskripsi_baru, id)
            )
            conn.commit()
            conn.close()
            return redirect("/dashboard")

        return render_template("update_product.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)