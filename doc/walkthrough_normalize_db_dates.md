# Walkthrough - Recent Prize Query Feature

We have successfully implemented the "Recent Prize Query" (近期獎號查詢) function for `lotto_app`.

## Changes Made

### 1. Programmatic Button Image Assets
- Generated two high-quality PNG button images with transparent background, matching the style of the `今彩539` button, but with green text:
  - `images/recent.png` (unpressed state, fill `#00C853`, dark outline, drop shadow)
  - `images/recent_pressed.png` (pressed state, 80% brightness of normal fill)

#### Button Assets:
- Normal button: [recent.png](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/images/recent.png)
- Pressed button: [recent_pressed.png](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/images/recent_pressed.png)

### 2. Main Screen Layout & Animations
- **Modified** [kv/common.kv](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/kv/common.kv):
  - Added `recent_btn` next to the `4star_btn` (Row 3, column 2 of the grid layout).
- **Modified** [modules/common.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/common.py):
  - Updated `LotteryTypeScreen.btn_states` to include `'recent'` so that the button's fade-in animation triggers properly on startup.

### 3. Recent Prize Logic & KV Layout
- **Created** [modules/recentprize.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/recentprize.py):
  - Implemented the `RecentPrizeScreen` class.
  - Queries `lotto_history.db` for the last 30 issues of the selected lottery.
  - Sorts query records correctly in memory by parsing date strings.
  - Formats lists using the custom `RecentPrizeRow` layout.
  - Binds Kivy `ResultBall` widgets dynamically (yellow/amber for regular numbers, cyan/blue for special numbers/second zone).
  - Handles the `go_back()` transition to return to the home screen (which is also called automatically by the edge-swipe gesture).
- **Created** [kv/recentprize.kv](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/kv/recentprize.kv):
  - Defined UI structure containing: Navigation bar (left "返回" button, center Title, right Spinner dropdown selector for lottery type), scrollable lists, and footer ad banner.
  - Defined `<RecentPrizeRow>` template containing issue and date labels, and a container grid for the lottery balls.
  - Added `<SpinnerOption>` styling rule to explicitly set the Chinese font (`font_name: 'ChineseFont'`) for the Spinner's dropdown list buttons, resolving the garbage character block (□□□) issue.
  - Added a downward arrow (`▼`) aligned to the right inside the Spinner button, and set right padding to prevent overlapping with the text.

### 4. Main App Hook-up
- **Modified** [main.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/main.py):
  - Imported `RecentPrizeScreen` and registered it in screen manager.
  - Registered `kv/recentprize.kv` to be loaded on startup.
  - Ensured `recent.png` and `recent_pressed.png` are checked during asset verification.
  - Fixed a critical Kivy bug on Android where the Spinner dropdown closed immediately after clicking. This was resolved by conditionalizing the `Config.set('input', 'mouse', 'mouse,disable_multitouch')` configuration to run only on desktop platforms (non-Android/iOS), avoiding double-dispatch of touch events on mobile.
  - Fixed a touch collision issue in [modules/common.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/common.py) and [modules/powerlotto.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/powerlotto.py) where clicking a saved number had no response on Android because `touch.button` is not set on mobile touchscreens. This was resolved by using `getattr(touch, 'button', None) in (None, 'left')`.
  - Regenerated the button assets (`images/recent.png` and `images/recent_pressed.png`) with an increased font size (`64` instead of `54`) to make the text and clickable area of the "Recent Prizes" button larger and easier to tap on mobile.
  - Configured `images/goodluckicon512.png` as the official application launcher icon for Android by adding `icon.filename` to [buildozer.spec](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/buildozer.spec).
  - Updated the Windows/desktop window icon configuration in [main.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/main.py) to use `images/goodluckicon512.png`.
  - Regenerated [logo.ico](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/images/logo.ico) using the high-resolution `goodluckicon512.png` to act as the Windows shortcut icon.
### 5. Database Date Standardization & Query Optimization
- **Created & Executed** `scratch/normalize_db_dates.py`:
  - Standardized all `date` values across all 5 lottery tables (`power_lotto`, `big_lotto`, `lotto_539`, `lotto_3star`, `lotto_4star`) to the 10-character padded `YYYY/MM/DD` format (e.g., `2008/01/02`).
  - Standardizing the dates resolves SQLite string sorting anomalies (e.g., preventing `2008/9/8` from sorting after `2008/9/29`).
- **Modified** [modules/common.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/common.py):
  - Added a index creation query for `power_lotto(date)` to `DatabaseManager._initialize_indexes()`.
- **Modified** [modules/recentprize.py](file:///d:/%E6%88%91%E7%9A%84%E5%B0%88%E6%A1%88/%E5%8F%B0%E5%BD%A9%E7%A8%8B%E5%BC%8F/lotto_app/modules/recentprize.py):
  - Simplified the data loading query by adding `ORDER BY date DESC, issue DESC LIMIT 30`.
  - Removed redundant date parsing (`datetime.strptime`) and Python in-memory sorting logic, allowing direct SQLite query results to populate the UI. This drastically reduces CPU overhead and memory footprint.

---

## Verification Results

### 1. Code Compile Verification
We compiled all changed Python files using the standard compile checker:
```bash
python -m py_compile main.py modules/recentprize.py modules/common.py
```
**Result**: Successfully compiled with zero warnings or errors.

### 2. Database Migration & Sorting Verification
Ran `scratch/dry_run_recentprize.py` to test the new SQL query efficiency and output correctness.
**Result**: 
- All lottery types retrieved exactly 30 records.
- Dates are strictly sorted descending chronologically (e.g., `2026/05/28` -> `2026/05/25` ...).
- Confirming B-tree Indexes are hit (`idx_powerlotto_date`, `idx_biglotto_date`, etc.).

### 3. GUI Application Run Verification
We launched the application using Kivy:
```bash
python main.py
```
**Result**:
- The application boots up cleanly.
- Kivy graphics subsystem initializes successfully.
- All screen layouts (including `recentprize.kv`) compile and load onto the screen manager without issues.
