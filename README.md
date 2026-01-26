# GitCanvas 🎨
[![Streamlit Live App](https://img.shields.io/badge/Streamlit-Live%20App-5314C4?logo=streamlit)](https://gitcanvas-dm.streamlit.app/)

GitCanvas is a Streamlit application that turns your GitHub contribution history into art. 
No more green squares, or any monotonous themes... visualize your code journey the way you want to.

## 🚀 Features

- **Artistic Themes**:
  - **Space**: Commits become stars in a vast void
  - **Gaming**: An 8-bit retro map where contributions build castles
  - **Music**: Your coding frequency visualized as audio waveforms
  - **Marvel**: A comic-book style hero profile based on your commit power (and moreeee... coming soon....)
- **AI Integration**: Placeholder logic ready for GenAI integration to analyze your "coding vibe".
- **Instant Export**: Download your art as SVG.

## Deployed application:
```
https://gitcanvas-dm.streamlit.app/
```

## 🛠 Installation

1. **Clone the repo** (or navigate to directory):
   ```bash
   cd gitcanvas
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**:
   ```bash
   streamlit run app.py
   ```

## 📂 Project Structure

- `app.py`: Main application logic.
- `themes/`: Contains the rendering logic for each theme.
  - `space.py`, `gaming.py`, `music.py`, `marvel.py`
- `ai/`: Placeholders for future AI/ML integration.
- `utils/`: Helper functions (GitHub API implementation).

## 🤝 Contributing

We welcome new themes! 
1. Create a file in `themes/` (e.g., `future.py`).
2. Implement a `render(data)` function that returns an SVG string.
3. Add it to `app.py`.

## 📜 License

MIT
