"""
แอป Android บริหารเงิน 50/30/20
สร้างด้วย Flet + SQLite
--------------------------------
วิธีติดตั้งและรัน:
  1. pip install flet
  2. python main.py
  3. หรือ build เป็น APK: flet build apk --project "MyBudgetApp"
"""

import flet as ft
import sqlite3
from datetime import datetime

# ====== ฐานข้อมูล (SQLite) ======
conn = sqlite3.connect("my_budget.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS records 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   date TEXT,
                   amount REAL,
                   spending REAL,
                   savings REAL,
                   reserve REAL,
                   note TEXT)''')
conn.commit()


def get_summary():
    """คำนวณยอดสะสมทั้งหมด"""
    cursor.execute("SELECT SUM(spending), SUM(savings), SUM(reserve) FROM records")
    row = cursor.fetchone()
    s, sv, r = row[0] or 0, row[1] or 0, row[2] or 0
    return s, sv, r, s + sv + r


def get_history(limit=10):
    """ดึงประวัติล่าสุด"""
    cursor.execute("SELECT date, amount, spending, savings, reserve FROM records ORDER BY date DESC LIMIT ?", (limit,))
    return cursor.fetchall()


# ====== ฟังก์ชันหลักของแอป ======
def main(page: ft.Page):
    page.title = "💰 บริหารเงิน 50/30/20"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20
    page.window.width = 420
    page.window.height = 740

    # ---- ตัวแปร UI ----
    amount_input = ft.TextField(
        label="💰 ยอดเงินเข้า (บาท)",
        keyboard_type=ft.KeyboardType.NUMBER,
        prefix_text="฿ ",
        border_color=ft.colors.PURPLE_300,
        focused_border_color=ft.colors.PURPLE_700,
        width=320,
    )

    note_input = ft.TextField(
        label="📝 โน้ต (เช่น เงินเดือน, โบนัส)",
        width=320,
        border_color=ft.colors.GREY_400,
    )

    result_card = ft.Card(
        visible=False,
        width=320,
        content=ft.Container(
            padding=20,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Text("✅ บันทึกสำเร็จ!", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_700),
                    ft.Row([ft.Text("🛍️ ใช้จ่าย 50%:", size=15), ft.Text("0", size=15, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT)],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([ft.Text("🏦 เก็บ 30%:", size=15), ft.Text("0", size=15, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT)],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([ft.Text("🛡️ สำรอง 20%:", size=15), ft.Text("0", size=15, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT)],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(),
                    ft.Row([ft.Text("📌 รวม:", size=16, weight=ft.FontWeight.BOLD), ft.Text("0", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.PURPLE_700, text_align=ft.TextAlign.RIGHT)],
                           alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ]
            )
        )
    )

    # Card สรุป
    summary_text = ft.Text("0.00", size=32, weight=ft.FontWeight.BOLD, color=ft.colors.PURPLE_700)
    spending_text = ft.Text("0.00", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.RED_600)
    savings_text = ft.Text("0.00", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_600)
    reserve_text = ft.Text("0.00", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_600)
    count_text = ft.Text("0", size=14, color=ft.colors.GREY_600)

    # History List
    history_list = ft.Column(spacing=4)

    def refresh_summary():
        s, sv, r, total = get_summary()
        summary_text.value = f"{total:,.2f}"
        spending_text.value = f"{s:,.2f}"
        savings_text.value = f"{sv:,.2f}"
        reserve_text.value = f"{r:,.2f}"
        cursor.execute("SELECT COUNT(*) FROM records")
        count_text.value = str(cursor.fetchone()[0])

        # อัปเดตประวัติ
        history_list.controls.clear()
        history = get_history(10)
        if history:
            for row in history:
                date_str, amt, sp, sv, rs = row
                history_list.controls.append(
                    ft.Container(
                        padding=ft.padding.symmetric(vertical=6, horizontal=8),
                        border=ft.border.all(0.5, ft.colors.GREY_300),
                        border_radius=8,
                        content=ft.Column([
                            ft.Text(date_str, size=11, color=ft.colors.GREY_600),
                            ft.Row([
                                ft.Text(f"💰 {amt:,.2f}", size=14, weight=ft.FontWeight.BOLD),
                                ft.Text(f"🛍️ {sp:,.2f}  🏦 {sv:,.2f}  🛡️ {rs:,.2f}", size=12, color=ft.colors.GREY_700),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, wrap=True),
                        ])
                    )
                )
        else:
            history_list.controls.append(
                ft.Text("📭 ยังไม่มีประวัติ", color=ft.colors.GREY_500, italic=True)
            )

        page.update()

    def save_data(e):
        try:
            total = float(amount_input.value.replace(",", ""))
            if total <= 0:
                raise ValueError
        except:
            page.show_snack_bar(ft.SnackBar(content=ft.Text("❌ กรุณากรอกตัวเลขที่มากกว่า 0"), bgcolor=ft.colors.RED_600))
            return

        s = total * 0.50
        sv = total * 0.30
        r = total * 0.20
        note = note_input.value.strip() or ""

        cursor.execute(
            "INSERT INTO records (date, amount, spending, savings, reserve, note) VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M"), total, s, sv, r, note)
        )
        conn.commit()

        # แสดงผลการบันทึก
        result_card.visible = True
        result_card.content.content.controls[1].controls[1].value = f"{s:,.2f} บาท"
        result_card.content.content.controls[2].controls[1].value = f"{sv:,.2f} บาท"
        result_card.content.content.controls[3].controls[1].value = f"{r:,.2f} บาท"
        result_card.content.content.controls[5].controls[1].value = f"{total:,.2f} บาท"
        page.update()

        amount_input.value = ""
        note_input.value = ""
        refresh_summary()

        page.show_snack_bar(ft.SnackBar(content=ft.Text(f"✅ บันทึกยอด {total:,.2f} บาท เรียบร้อย!"), bgcolor=ft.colors.GREEN_600))

    def reset_data(e):
        def confirm_reset(e2):
            cursor.execute("DELETE FROM records")
            conn.commit()
            result_card.visible = False
            page.close(dlg)
            refresh_summary()
            page.show_snack_bar(ft.SnackBar(content=ft.Text("🗑️ ล้างข้อมูลเรียบร้อย"), bgcolor=ft.colors.BLUE_600))

        dlg = ft.AlertDialog(
            title=ft.Text("⚠️ ยืนยันล้างข้อมูล"),
            content=ft.Text("ข้อมูลทั้งหมดจะถูกลบ การกระทำนี้ไม่สามารถย้อนกลับได้"),
            actions=[
                ft.TextButton("ยกเลิก", on_click=lambda e: page.close(dlg)),
                ft.ElevatedButton("ยืนยัน ล้างข้อมูล", color=ft.colors.WHITE, bgcolor=ft.colors.RED_600, on_click=confirm_reset),
            ]
        )
        page.open(dlg)

    # ====== ส่วนประกอบ UI ======
    # ส่วนหัว
    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("💰 บริหารเงิน", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.PURPLE_700),
                ft.Text("สัดส่วน 50/30/20", size=16, color=ft.colors.GREY_600),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            margin=ft.margin.only(bottom=16),
        )
    )

    # Card: บันทึกรายรับ
    page.add(
        ft.Card(
            width=360,
            content=ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("📥 บันทึกรายรับใหม่", size=18, weight=ft.FontWeight.BOLD),
                    amount_input,
                    note_input,
                    ft.ElevatedButton(
                        "💾 บันทึกและแบ่งเงิน",
                        width=280,
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.PURPLE_600,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12)),
                        on_click=save_data,
                    ),
                    result_card,
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12)
            )
        )
    )

    # Card: สรุปยอดสะสม
    page.add(
        ft.Container(height=10),
        ft.Card(
            width=360,
            content=ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("📊 สรุปยอดสะสม", size=18, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Text("฿", size=20, color=ft.colors.PURPLE_600),
                        summary_text,
                        ft.Text("บาท", size=16, color=ft.colors.GREY_600),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Divider(),
                    ft.Row([
                        ft.Column([ft.Text("🛍️ ใช้จ่าย", size=13, color=ft.colors.GREY_600), spending_text], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Column([ft.Text("🏦 เก็บ", size=13, color=ft.colors.GREY_600), savings_text], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        ft.Column([ft.Text("🛡️ สำรอง", size=13, color=ft.colors.GREY_600), reserve_text], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                    ft.Divider(),
                    ft.Row([
                        ft.Text(f"ℹ️ จำนวนครั้ง: ", size=13, color=ft.colors.GREY_600),
                        count_text,
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)
            )
        )
    )

    # Card: ประวัติ
    page.add(
        ft.Container(height=10),
        ft.Card(
            width=360,
            content=ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("📜 ประวัติล่าสุด", size=18, weight=ft.FontWeight.BOLD),
                    history_list,
                ])
            )
        )
    )

    # ปุ่มล้างข้อมูล
    page.add(
        ft.Container(height=10),
        ft.ElevatedButton(
            "🗑️ ล้างข้อมูลทั้งหมด",
            width=360,
            color=ft.colors.RED_600,
            bgcolor=ft.colors.RED_50,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), side=ft.BorderSide(1, ft.colors.RED_300)),
            on_click=reset_data,
        ),
        ft.Container(
            content=ft.Text("💰 แบ่งเงินตามสัดส่วน 50/30/20 ทุกครั้งที่มีรายรับ • ข้อมูลถูกบันทึกในเครื่อง", size=11, color=ft.colors.GREY_500, italic=True),
            margin=ft.margin.only(top=10, bottom=10),
            alignment=ft.alignment.center,
        )
    )

    # โหลดข้อมูลครั้งแรก
    refresh_summary()


if __name__ == "__main__":
    ft.app(target=main)