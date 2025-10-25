import re
import qrcode
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

# color
HEX6 = re.compile(r"^#[0-9a-fA-F]{6}$")
def safe_color(c: str, fallback: str = "#1e1e2e") -> str:
    return c if isinstance(c, str) and HEX6.match(c) else fallback

def darken(hex_color: str, factor: float = 0.85) -> str:
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    r = max(0, min(255, int(r * factor)))
    g = max(0, min(255, int(g * factor)))
    b = max(0, min(255, int(b * factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


BG      = safe_color("#1e1e2e")   # bg
CARD    = safe_color("#2e2e3e")   # card
FG      = safe_color("#ffffff")   # txt
ACCENT  = safe_color("#4caf50")   # gen
PRIMARY = safe_color("#2196f3")   # save
DANGER  = safe_color("#ef4444")   # clear

QR_SIZE = 320


def make_hover(btn: tk.Button, normal_bg: str):
    hover_bg = darken(normal_bg, 0.85)
    btn.config(cursor="hand2", bg=normal_bg, activebackground=hover_bg)
    def _in(_):  btn.configure(bg=hover_bg)
    def _out(_): btn.configure(bg=normal_bg)
    btn.bind("<Enter>", _in)
    btn.bind("<Leave>", _out)


class QRApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Link → QR Code")
        self.root.geometry("560x760")
        self.root.minsize(520, 640)
        self.root.configure(bg=BG)

        # header
        tk.Label(root, text="Link → QR Code",
                 font=("Segoe UI", 20, "bold"), fg=FG, bg=BG).pack(pady=(18, 8))
        tk.Label(root, text="Generate QR",
                 font=("Segoe UI", 10), fg="#cbd5e1", bg=BG).pack(pady=(0, 14))

        # Input + Buttons
        card = tk.Frame(root, bg=CARD, bd=0, highlightthickness=0)
        card.pack(fill="x", padx=24, pady=8)

        tk.Label(card, text="Link / URL", font=("Segoe UI", 10, "bold"),
                 fg=FG, bg=CARD).pack(anchor="w", padx=16, pady=(16, 6))

        self.url = tk.StringVar()
        entry = tk.Entry(card, textvariable=self.url, font=("Segoe UI", 12),
                         bg=BG, fg=FG, insertbackground=FG, relief="flat")
        entry.pack(fill="x", padx=16, pady=(0, 12), ipady=8)
        entry.focus_set()

        btn_row = tk.Frame(card, bg=CARD)
        btn_row.pack(fill="x", padx=16, pady=(0, 16))

        gen_btn = tk.Button(btn_row, text="Generate QR", font=("Segoe UI", 10, "bold"),
                            bg=ACCENT, fg="white", relief="flat",
                            padx=14, pady=8, command=self.generate)
        gen_btn.pack(side="left")
        make_hover(gen_btn, ACCENT)

        save_btn = tk.Button(btn_row, text="Save PNG", font=("Segoe UI", 10, "bold"),
                             bg=PRIMARY, fg="white", relief="flat",
                             padx=14, pady=8, command=self.save)
        save_btn.pack(side="left", padx=10)
        make_hover(save_btn, PRIMARY)

        clear_btn = tk.Button(btn_row, text="Clear", font=("Segoe UI", 10, "bold"),
                              bg=DANGER, fg="white", relief="flat",
                              padx=14, pady=8, command=self.clear)
        clear_btn.pack(side="right")
        make_hover(clear_btn, DANGER)

        # Auto-generate toggle
        toggle_row = tk.Frame(card, bg=CARD)
        toggle_row.pack(fill="x", padx=16, pady=(0, 12))

        self.auto_var = tk.BooleanVar(value=True)  # auto
        auto_chk = tk.Checkbutton(
            toggle_row, text="Auto-generate (real-time)",
            variable=self.auto_var,
            onvalue=True, offvalue=False,
            bg=CARD, fg=FG, selectcolor=CARD,
            activebackground=CARD, activeforeground=FG,
            font=("Segoe UI", 10)
        )
        auto_chk.pack(side="left")

        self.status = tk.Label(toggle_row, text="", font=("Segoe UI", 9),
                               fg="#94a3b8", bg=CARD)
        self.status.pack(side="right")

        # Card: Preview 
        prev_card = tk.Frame(root, bg=CARD, bd=0, highlightthickness=0)
        prev_card.pack(fill="both", expand=True, padx=24, pady=8)
        tk.Label(prev_card, text="Preview", font=("Segoe UI", 10, "bold"),
                 fg=FG, bg=CARD).pack(anchor="w", padx=16, pady=(16, 8))
        self.canvas = tk.Label(prev_card, bg=CARD)
        self.canvas.pack(padx=16, pady=(0, 16), expand=True)

        # State
        self.qr_pil = None
        self.qr_tk = None

        self._debounce_id = None
        self._debounce_ms = 300

        self.url.trace_add("write", self._on_url_change)

        tk.Label(root, text="© link2qr • made with Python + Tkinter by daxk",
                 font=("Segoe UI", 9), fg="#94a3b8", bg=BG).pack(pady=(0, 10))


    def _on_url_change(self, *args):
        """ถูกเรียกทุกครั้งที่ค่าของ self.url เปลี่ยน"""
        if not self.auto_var.get():

            self.status.configure(text="Auto: Off")
            return

        # autogen 
        if self._debounce_id is not None:
            try:
                self.root.after_cancel(self._debounce_id)
            except Exception:
                pass
            self._debounce_id = None


        self._debounce_id = self.root.after(self._debounce_ms, self._auto_generate)

    def _auto_generate(self):
        self._debounce_id = None
        url = (self.url.get() or "").strip()
        if not url:

            self._clear_preview_only()
            self.status.configure(text="Waiting for input…")
            return
        self.status.configure(text="Auto: Generating…")
        ok = self._do_generate(url)
        self.status.configure(text="Auto: Ready" if ok else "Auto: Invalid URL")

    def _do_generate(self, url: str) -> bool:
        """ทำงานสร้าง QR จริง ๆ; return True ถ้าสำเร็จ"""
        try:
            qr = qrcode.QRCode(
                version=None, box_size=10, border=2,
                error_correction=qrcode.constants.ERROR_CORRECT_M
            )
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
            img = img.resize((QR_SIZE, QR_SIZE))

            self.qr_pil = img
            self.qr_tk = ImageTk.PhotoImage(img)
            self.canvas.configure(image=self.qr_tk)
            return True
        except Exception as e:
            self.status.configure(text=f"Error: {e}")
            return False


    # ปุ่ม

    def generate(self):
        """ปุ่ม Generate QR (ใช้งานได้เหมือนเดิม)"""
        url = (self.url.get() or "").strip()
        if not url:
            messagebox.showwarning("Hey", "Paste link first!")
            return
        ok = self._do_generate(url)
        if ok:
            self.status.configure(text="Generated manually")

    def save(self):
        if self.qr_pil is None:
            messagebox.showinfo("Not yet created", "Generate a QR before saving")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG image", "*.png")],
            title="Save file QR"
        )
        if path:
            self.qr_pil.save(path)
            messagebox.showinfo("success", f"Saved:\n{path}")

    def clear(self):
        self.url.set("")
        self._clear_preview_only()
        self.status.configure(text="Cleared")


    # Helpers

    def _clear_preview_only(self):
        self.qr_pil = None
        self.qr_tk = None
        self.canvas.configure(image="", text="")

    
        if self._debounce_id is not None:
            try:
                self.root.after_cancel(self._debounce_id)
            except Exception:
                pass
            self._debounce_id = None


if __name__ == "__main__":
    root = tk.Tk()
    root.configure(bg=BG)
    app = QRApp(root)
    root.mainloop()
