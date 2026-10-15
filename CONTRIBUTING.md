# GitCanvas Contributor Guide 📚

Complete guide for setting up GitCanvas locally and creating custom themes.

```New themes, new cards and new elements to personalise your GitHub Readme's are always welcome!!!```

---

## 🚀 Quick Setup

### Prerequisites
- Python 3.8+
- Git

### Installation
```bash
# Clone and install
git clone https://github.com/devanshi14malhotra/GitCanvas.git
cd GitCanvas
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

App opens at `http://localhost:8501`

### Optional: Add GitHub Token
Create `.env` file for higher API limits (5,000/hour vs 60/hour):
```bash
GITHUB_TOKEN_1=
GITHUB_TOKEN_2=
GITHUB_TOKEN_3=
```

---

## 📁 Key Directories

- **`themes/`** - Theme definitions and custom renderers
- **`generators/`** - SVG card generators for different stats
- **`utils/`** - GitHub API client, caching, validation
- **`app.py`** - Main Streamlit application
- **`api/`** - FastAPI backend endpoints

---

## 🎨 Creating a New Theme

### Step 1: Add Theme Colors to `themes/styles.py`

```python
THEMES = {
    # ... existing themes ...
    
    "YourThemeName": {
        "bg_color": "#0d1117",
        "border_color": "#30363d",
        "title_color": "#58a6ff",
        "text_color": "#c9d1d9",
        "icon_color": "#8b949e",
        "font_family": "Segoe UI, Ubuntu, Sans-Serif"
    }
}
```

### Step 2: Create Custom Renderer (Optional)

For special visualizations (like Matrix rain or Gaming snake), create `themes/yourtheme.py`:

```python
import svgwrite

def render(data, theme, width=600, height=200):
    """
    Custom visualization for YourTheme.
    
    Args:
        data: Contains 'username' and 'contributions' list
        theme: Theme colors from styles.py
        width/height: SVG dimensions
    
    Returns:
        str: SVG string
    """
    dwg = svgwrite.Drawing(size=(width, height))
    
    # Background
    dwg.add(dwg.rect(insert=(0, 0), size=(width, height), 
                     fill=theme["bg_color"]))
    
    # Get real contribution data
    contributions = data.get("contributions", [])
    username = data.get("username", "User")
    
    # Your visualization logic
    for day in contributions:
        count = day.get("count", 0)
        if count <= 0:
            continue
        # Draw based on contribution count
    
    return dwg.tostring()
```

### Step 3: Integrate into `generators/contrib_card.py`

```python
def draw_contrib_card(data, theme_name="Default", ...):
    # ... existing code ...
    
    elif original_theme_name == "YourThemeName":
        from themes import yourtheme
        svg = yourtheme.render(data, theme)
        return svg
```

### Step 4: Test

```bash
streamlit run app.py
# Select your theme and test with real usernames
```
---

## ✅ Theme Best Practices

**DO:**
- Use real contribution data: `data.get("contributions", [])`
- Skip zero contributions: `if count <= 0: continue`
- Add docstrings and comments
- Test with real usernames (e.g., "torvalds")
- Use theme colors: `theme["bg_color"]`

**DON'T:**
- Generate fake/random data
- Show activity where none exists
- Remove documentation
- Hardcode colors

---

## 📝 Contributing Guidelines

### Pull Request Process
1. Fork repository and create feature branch
2. Make focused changes (one feature per PR)
3. Test with multiple GitHub usernames
4. Write clear commit messages
5. Submit PR with description

### Code Standards
- Write clean, documented code
- Follow PEP 8 style
- Always use real GitHub data
- Handle edge cases gracefully

### Commit Format (example)
```
feat: add Ocean theme with fish visualization
fix: resolve API rate limiting issue
docs: update tutorial with examples
```

---

## 📚 Resources

- [GitHub API Docs](https://docs.github.com/en/rest)
- [SVGwrite Docs](https://svgwrite.readthedocs.io/)
- [Streamlit Docs](https://docs.streamlit.io/)

---

**Happy Contributing! 🎨✨**

If you create an awesome theme, we'd love to see it. Don't hesitate to submit a PR!
