from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "rahasia"


def is_admin():
    return session.get("username") is not None and session.get("role") == "admin"


def render_message(title, message, kind="error", back_url="/dashboard", back_label="Kembali"):
    return render_template(
        "message.html",
        title=title,
        message=message,
        kind=kind,
        back_url=back_url,
        back_label=back_label,
    )


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
            if check_password_hash(user[2], password):
                session["username"] = user[1]
                session["role"] = user[3]
                return redirect("/dashboard")
            return render_message("Login Gagal", "Password salah", "error", "/login", "Coba lagi")

        return render_message("Login Gagal", "Username tidak ditemukan", "error", "/login", "Coba lagi")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed = generate_password_hash(password)

        conn = sqlite3.connect("marketplace.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
                """,
                (username, hashed, "user")
            )
            conn.commit()
            conn.close()
            return redirect("/login")
        except sqlite3.IntegrityError:
            conn.close()
            return render_message("Registrasi Gagal", "Username sudah digunakan", "error", "/register", "Coba lagi")

    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("marketplace.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    user = cursor.fetchall()
    cursor.execute(
        "SELECT * FROM products WHERE penjual = ?",
        (session["username"],)
    )
    products = cursor.fetchall()
    cursor.execute(
        "SELECT saldo FROM users WHERE username = ?",
        (session["username"],)
    )
    saldo = cursor.fetchone()
    conn.close()

    saldo = int(saldo[0]) if saldo else 0
    username = session["username"]
    return render_template(
        "dashboard.html",
        nama_pengguna=username,
        jumlah_user=len(user),
        daftar_user=user,
        daftar_produk=products,
        saldo=saldo,
        role=session.get("role")
    )


@app.route("/delete", methods=["POST", "GET"])
def delete():
    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":
        password = request.form["password"]
        conn = sqlite3.connect("marketplace.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password FROM users WHERE username = ?",
            (session["username"],)
        )
        hasil = cursor.fetchone()

        if hasil and check_password_hash(hasil[0], password):
            cursor.execute(
                "DELETE FROM users WHERE username = ?",
                (session["username"],)
            )
            conn.commit()
            conn.close()
            session.clear()
            return redirect("/")

        conn.close()
        return render_message("Hapus Akun Gagal", "Password salah", "error", "/delete", "Coba lagi")

    return render_template("delete.html")


@app.route("/change-password", methods=["POST", "GET"])
def change_password():
    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":
        password = request.form["password"]
        hashed = generate_password_hash(password)
        conn = sqlite3.connect("marketplace.db")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password = ? WHERE username = ?",
            (hashed, session["username"])
        )
        conn.commit()
        conn.close()
        return render_message("Berhasil", "Password akun berhasil diubah", "success", "/dashboard", "Kembali ke dashboard")

    return render_template("change_password.html")


@app.route("/change-name", methods=["POST", "GET"])
def change_name():
    if "username" not in session:
        return redirect("/login")

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


@app.route("/add-product", methods=["GET", "POST"])
def add_product():
    if "username" not in session:
        return redirect("/login")

    if request.method == "POST":
        product = request.form["nama produk"]
        try:
            price = int(request.form["harga"])
        except ValueError:
            return render_message("Input Tidak Valid", "Harga harus berupa angka", "error", "/add-product", "Coba lagi")
        description = request.form["deskripsi"]

        conn = sqlite3.connect("marketplace.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO products (nama, harga, deskripsi, penjual)
            VALUES (?, ?, ?, ?)
            """,
            (product, price, description, session["username"])
        )
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    return render_template("add_product.html")


@app.route("/update-product/<int:id>", methods=["GET", "POST"])
def update_product(id):
    conn = sqlite3.connect("marketplace.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM products WHERE id = ? AND penjual = ?
        """,
        (id, session["username"])
    )
    products = cursor.fetchone()

    if products is None:
        conn.close()
        return redirect("/dashboard")

    if request.method == "POST":
        nama = products[1]
        harga = products[2]
        deskripsi = products[3]
        nama_baru = request.form["nama produk"]
        harga_input = request.form["harga"]

        if harga_input == "":
            harga_baru = harga
        else:
            try:
                harga_baru = int(harga_input)
            except ValueError:
                conn.close()
                return render_message("Input Tidak Valid", "Harga harus berupa angka", "error", f"/update-product/{id}", "Coba lagi")

        deskripsi_baru = request.form["deskripsi"]
        if nama_baru == "":
            nama_baru = nama
        if deskripsi_baru == "":
            deskripsi_baru = deskripsi

        cursor.execute(
            """
            UPDATE products SET nama = ?, harga = ?, deskripsi = ?
            WHERE id = ? AND penjual = ?
            """,
            (nama_baru, harga_baru, deskripsi_baru, id, session["username"])
        )
        conn.commit()
        conn.close()
        return redirect("/dashboard")

    conn.close()
    return render_template("update_product.html")


@app.route("/delete-product/<int:id>", methods=["GET", "POST"])
def delete_product(id):
    conn = sqlite3.connect("marketplace.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT * FROM products WHERE id = ? AND penjual = ?
        """,
        (id, session["username"])
    )
    products = cursor.fetchone()

    if products is None:
        conn.close()
        return redirect("/dashboard")

    if request.method == "POST":
        pilihan = request.form.get("konfirmasi")
        if pilihan == "ya":
            cursor.execute(
                """
                DELETE FROM products WHERE id = ? AND penjual = ?
                """,
                (id, session["username"])
            )
            conn.commit()
        conn.close()
        return redirect("/dashboard")

    conn.close()
    return render_template("delete_product.html")


@app.route("/marketplace", methods=["GET", "POST"])
def marketplace():
    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("marketplace.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    buyer = session["username"]

    if request.method == "POST":
        product_id = request.form.get("product_id")
        if not product_id:
            conn.close()
            return render_message("Aksi Gagal", "product_id tidak dikirim", "error", "/marketplace", "Kembali")

        cursor.execute(
            "SELECT * FROM cart WHERE pembeli = ? AND product_id = ?",
            (buyer, product_id)
        )
        cek = cursor.fetchone()
        if cek is not None:
            conn.close()
            return render_message("Keranjang", "Produk sudah ada di keranjang", "error", "/marketplace", "Kembali ke marketplace")

        cursor.execute(
            "INSERT INTO cart (pembeli, product_id) VALUES (?, ?)",
            (buyer, product_id)
        )
        conn.commit()
        conn.close()
        return redirect("/cart")

    conn.close()
    return render_template(
        "marketplace.html",
        daftar_produk=products,
        pembeli=buyer
    )


@app.route("/cart", methods=["GET", "POST"])
def cart():
    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("marketplace.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT products.id, products.nama, products.harga, products.deskripsi, products.penjual
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.pembeli = ?
        """,
        (session["username"],)
    )
    produk = cursor.fetchall()
    conn.close()

    return render_template("cart.html", keranjang=produk)


@app.route("/admin")
def admin_dashboard():
    if not is_admin():
        if "username" not in session:
            return redirect("/login")
        return redirect("/dashboard")

    conn = sqlite3.connect("marketplace.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, role, saldo FROM users")
    users = cursor.fetchall()
    cursor.execute("SELECT id, nama, harga, deskripsi, penjual FROM products")
    products = cursor.fetchall()
    conn.close()

    return render_template("admin.html", users=users, products=products)


@app.route("/admin/user/<int:id>/edit", methods=["GET", "POST"])
def admin_edit_user(id):
    if not is_admin():
        if "username" not in session:
            return redirect("/login")
        return redirect("/dashboard")

    conn = sqlite3.connect("marketplace.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password, role, saldo FROM users WHERE id = ?", (id,))
    user = cursor.fetchone()

    if user is None:
        conn.close()
        return redirect("/admin")

    if request.method == "POST":
        old_username = user[1]
        username = request.form["username"].strip()
        role = request.form["role"].strip()
        saldo_input = request.form["saldo"].strip()
        new_password = request.form.get("password", "").strip()

        if username == "" or role == "" or saldo_input == "":
            conn.close()
            return render_message("Input Tidak Valid", "Semua field wajib diisi", "error", f"/admin/user/{id}/edit", "Coba lagi")

        try:
            saldo = int(saldo_input)
        except ValueError:
            conn.close()
            return render_message("Input Tidak Valid", "Saldo harus berupa angka", "error", f"/admin/user/{id}/edit", "Coba lagi")

        if new_password:
            password_hash = generate_password_hash(new_password)
        else:
            password_hash = user[2]

        try:
            cursor.execute(
                "UPDATE users SET username = ?, password = ?, role = ?, saldo = ? WHERE id = ?",
                (username, password_hash, role, saldo, id)
            )
        except sqlite3.IntegrityError:
            conn.close()
            return render_message("Input Tidak Valid", "Username sudah digunakan", "error", f"/admin/user/{id}/edit", "Coba lagi")

        if old_username != username:
            cursor.execute("UPDATE products SET penjual = ? WHERE penjual = ?", (username, old_username))
            cursor.execute("UPDATE cart SET pembeli = ? WHERE pembeli = ?", (username, old_username))
            if session.get("username") == old_username:
                session["username"] = username

        conn.commit()
        conn.close()
        return redirect("/admin")

    conn.close()
    return render_template("edit_user.html", user=user)


@app.route("/admin/user/<int:id>/delete", methods=["POST"])
def admin_delete_user(id):
    if not is_admin():
        if "username" not in session:
            return redirect("/login")
        return redirect("/dashboard")

    conn = sqlite3.connect("marketplace.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, username FROM users WHERE id = ?", (id,))
    user = cursor.fetchone()

    if user is None:
        conn.close()
        return redirect("/admin")

    username = user[1]
    cursor.execute("SELECT id FROM products WHERE penjual = ?", (username,))
    product_ids = [row[0] for row in cursor.fetchall()]

    cursor.execute("DELETE FROM cart WHERE pembeli = ?", (username,))
    if product_ids:
        placeholders = ",".join("?" for _ in product_ids)
        cursor.execute(f"DELETE FROM cart WHERE product_id IN ({placeholders})", product_ids)
    cursor.execute("DELETE FROM products WHERE penjual = ?", (username,))
    cursor.execute("DELETE FROM users WHERE id = ?", (id,))

    conn.commit()
    conn.close()
    return redirect("/admin")


@app.route("/admin/product/<int:id>/edit", methods=["GET", "POST"])
def admin_edit_product(id):
    if not is_admin():
        if "username" not in session:
            return redirect("/login")
        return redirect("/dashboard")

    conn = sqlite3.connect("marketplace.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, nama, harga, deskripsi, penjual FROM products WHERE id = ?", (id,))
    product = cursor.fetchone()
    cursor.execute("SELECT username FROM users")
    users = cursor.fetchall()

    if product is None:
        conn.close()
        return redirect("/admin")

    if request.method == "POST":
        nama = request.form["nama"].strip()
        harga_input = request.form["harga"].strip()
        deskripsi = request.form["deskripsi"].strip()
        penjual = request.form["penjual"].strip()

        if nama == "" or harga_input == "" or deskripsi == "" or penjual == "":
            conn.close()
            return render_message("Input Tidak Valid", "Semua field wajib diisi", "error", f"/admin/product/{id}/edit", "Coba lagi")

        try:
            harga = int(harga_input)
        except ValueError:
            conn.close()
            return render_message("Input Tidak Valid", "Harga harus berupa angka", "error", f"/admin/product/{id}/edit", "Coba lagi")

        cursor.execute("SELECT 1 FROM users WHERE username = ?", (penjual,))
        seller_exists = cursor.fetchone()
        if seller_exists is None:
            conn.close()
            return render_message("Input Tidak Valid", "Penjual tidak ditemukan", "error", f"/admin/product/{id}/edit", "Coba lagi")

        cursor.execute(
            "UPDATE products SET nama = ?, harga = ?, deskripsi = ?, penjual = ? WHERE id = ?",
            (nama, harga, deskripsi, penjual, id)
        )
        conn.commit()
        conn.close()
        return redirect("/admin")

    conn.close()
    return render_template("edit_product.html", product=product, users=users)


@app.route("/admin/product/<int:id>/delete", methods=["POST"])
def admin_delete_product(id):
    if not is_admin():
        if "username" not in session:
            return redirect("/login")
        return redirect("/dashboard")

    conn = sqlite3.connect("marketplace.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE product_id = ?", (id,))
    cursor.execute("DELETE FROM products WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")


@app.route("/checkout/<int:id>", methods=["POST"])
def checkout(id):
    if "username" not in session:
        return redirect("/login")

    buyer = session["username"]
    conn = sqlite3.connect("marketplace.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT products.id, products.harga, products.penjual
        FROM cart
        JOIN products ON cart.product_id = products.id
        WHERE cart.pembeli = ? AND products.id = ?
        """,
        (buyer, id)
    )
    product = cursor.fetchone()

    if product is None:
        conn.close()
        return render_message("Checkout Gagal", "Produk tidak ditemukan di keranjang", "error", "/cart", "Kembali ke keranjang")

    product_id = product[0]
    price = int(product[1])
    seller = product[2]

    cursor.execute(
        "SELECT saldo FROM users WHERE username = ?",
        (buyer,)
    )
    buyer_balance_row = cursor.fetchone()
    buyer_balance = int(buyer_balance_row[0]) if buyer_balance_row else 0

    if buyer_balance < price:
        conn.close()
        return render_message("Checkout Gagal", "Saldo tidak cukup", "error", "/cart", "Kembali ke keranjang")

    cursor.execute(
        "SELECT saldo FROM users WHERE username = ?",
        (seller,)
    )
    seller_balance_row = cursor.fetchone()
    seller_balance = int(seller_balance_row[0]) if seller_balance_row else 0

    new_buyer_balance = buyer_balance - price
    new_seller_balance = seller_balance + price

    cursor.execute(
        "UPDATE users SET saldo = ? WHERE username = ?",
        (new_buyer_balance, buyer)
    )
    cursor.execute(
        "UPDATE users SET saldo = ? WHERE username = ?",
        (new_seller_balance, seller)
    )
    cursor.execute(
        "DELETE FROM cart WHERE pembeli = ? AND product_id = ?",
        (buyer, product_id)
    )
    cursor.execute(
        "UPDATE products SET penjual = ? WHERE id = ?",
        (buyer, product_id)
    )

    conn.commit()
    conn.close()
    return redirect("/cart")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)