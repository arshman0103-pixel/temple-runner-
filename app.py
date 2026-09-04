import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Temple Runner 3D", layout="wide")

st.title("🏃‍♂️ Temple Runner 3D")
st.write("Play directly in your browser below! Use Arrow Keys or WASD to move, jump, and slide.")

# Pygame WebAssembly embed frame
iframe_code = """
<iframe src="https://pygame.hogwarts.zone/" width="800" height="620" style="border:none;"></iframe>
"""

# Embed Pygame canvas component
components.html(iframe_code, height=650)
