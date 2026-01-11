Tell it like it is: **this page is a landmine**.
When shapes are stacked, used as masks, and overlapping visuals, moving things “a little bit” will break something you can’t see. You’re right to be cautious.

Below are **safe, proven ways** to deal with this without wrecking the report.

---

## 1️⃣ First rule: work on a copy (non-negotiable)

Before touching anything:

* **Save As → new PBIX**
* Turn on **File → Options → Preview features → (nothing special needed)**
  Just don’t work on the only copy.

This is not paranoia. Power BI has **no undo history across sessions**.

---

## 2️⃣ Use the Selection Pane like an X-ray (mandatory)

If you’re not using this already, stop and do this first:

**View → Selection pane**

Why this matters:

* Shows **every shape, button, visual**
* Shows **layer order (top → bottom)**
* Lets you **hide visuals temporarily** 👈 critical
* Lets you **lock visuals**

### Safe workflow

1. Open **Selection pane**
2. **Rename visuals** (slow but worth it)

   * `BG_Header`
   * `Mask_Main`
   * `Btn_Filter_01`
3. **Hide** big background/mask shapes
   (eye icon)
   → suddenly you’ll see what’s really there

This alone usually reveals:

> “Oh… this shape was covering 5 things.”

---

## 3️⃣ Lock everything that should NOT move

This is how you avoid accidental disasters.

In **Selection pane**:

* Lock:

  * Background rectangles
  * Mask shapes
  * Decorative layers
* Leave unlocked:

  * Only the items you truly want to move

Now accidental clicks won’t drag half the page.

---

## 4️⃣ Move in groups — never one by one

If you move visuals individually, you **will** misalign something.

### Safe method

1. In **Selection pane**, multi-select all visuals **below** the insertion point
2. **Group** them (Ctrl + G)
3. Move the group **down together**
4. Insert the new table visual
5. Ungroup if needed

This keeps:

* Relative spacing
* Mask alignment
* Button overlays intact

---

## 5️⃣ Use “Bring forward / Send backward” intentionally

When you add the new table:

* It will probably be **hidden**
* Or it will **cover buttons**

Fix this deliberately:

* Select new visual
* Right-click:

  * Bring to front (temporarily)
* Then send it **just above** the correct background layer

Do NOT eyeball this.
Check layer order in **Selection pane**.

---

## 6️⃣ Temporarily remove masks (advanced but safe)

If shapes are used as **visual masks**:

1. Hide the mask shape
2. Do layout work
3. Show mask again
4. Adjust z-order if needed

Never resize masked visuals while the mask is hidden — only reposition.

---

## 7️⃣ Use Snap-to-grid OFF (important)

For dense layouts:

* **View → Snap to grid → OFF**
* **View → Show gridlines → OFF**

Snap will cause tiny unwanted jumps that break alignment with overlays.

---

## 8️⃣ Last-resort but clean solution (often best)

If the page is truly unmaintainable:

### Duplicate the page

* Right-click page → Duplicate
* Strip it down:

  * Remove decorative shapes
  * Rebuild layout cleanly
* Keep original page as reference / backup

Yes, this feels wasteful.
No, it’s not. It’s **technical debt payoff**.

---

## 9️⃣ Hard truth (experience talking)

Pages built like this:

* Are fragile
* Do not scale
* Should never have been designed this way

If this is a long-term report:
👉 **plan a redesign using containers**

* Use fewer shapes
* Use alignment + spacing
* Avoid “shape as mask” patterns

---

## If you want next steps

I can:

* Give you a **step-by-step “surgical” checklist** while inserting the table
* Suggest a **future-proof layout pattern**
* Explain how to replace shape-based masking safely

Just say which direction you want to go.
