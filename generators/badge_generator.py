
TECH_STACK = {
    "Languages": {
        "Python": {"color": "3776AB", "logo": "python"},
        "JavaScript": {"color": "F7DF1E", "logo": "javascript"},
        "TypeScript": {"color": "3178C6", "logo": "typescript"},
        "Java": {"color": "007396", "logo": "java"},
        "C++": {"color": "00599C", "logo": "cplusplus"},
        "Rust": {"color": "000000", "logo": "rust"},
        "Go": {"color": "00ADD8", "logo": "go"},
        "C#": {"color": "239120", "logo": "csharp"},
        "PHP": {"color": "777BB4", "logo": "php"},
        "Ruby": {"color": "CC342D", "logo": "ruby"},
        "Swift": {"color": "FA7343", "logo": "swift"},
        "Kotlin": {"color": "7F52FF", "logo": "kotlin"},
    },
    "Frontend": {
        "React": {"color": "61DAFB", "logo": "react"},
        "Vue": {"color": "4FC08D", "logo": "vuedotjs"},
        "Angular": {"color": "DD0031", "logo": "angular"},
        "Streamlit": {"color": "FF4B4B", "logo": "streamlit"},
        "TailwindCSS": {"color": "06B6D4", "logo": "tailwindcss"},
        "HTML5": {"color": "E34F26", "logo": "html5"},
        "CSS3": {"color": "1572B6", "logo": "css3"},
        "Sass": {"color": "CC6699", "logo": "sass"},
        "Bootstrap": {"color": "7952B3", "logo": "bootstrap"},
        "Next.js": {"color": "000000", "logo": "nextdotjs"},
        "Nuxt.js": {"color": "00DC82", "logo": "nuxtdotjs"},
        "Svelte": {"color": "FF3E00", "logo": "svelte"},
    },
    "Backend & DB": {
        "Node.js": {"color": "339933", "logo": "nodedotjs"},
        "Django": {"color": "092E20", "logo": "django"},
        "FastAPI": {"color": "009688", "logo": "fastapi"},
        "PostgreSQL": {"color": "4169E1", "logo": "postgresql"},
        "MongoDB": {"color": "47A248", "logo": "mongodb"},
        "Firebase": {"color": "FFCA28", "logo": "firebase"},
    },
    "Tools": {
        "Git": {"color": "F05032", "logo": "git"},
        "Docker": {"color": "2496ED", "logo": "docker"},
        "AWS": {"color": "232F3E", "logo": "amazonwebservices"},
        "Figma": {"color": "F24E1E", "logo": "figma"},
        "Linux": {"color": "FCC624", "logo": "linux"},
        "VS Code": {"color": "007ACC", "logo": "visualstudiocode"},
        "Postman": {"color": "FF6C37", "logo": "postman"},
        "Kubernetes": {"color": "326CE5", "logo": "kubernetes"},
        "Jenkins": {"color": "D24939", "logo": "jenkins"},
        "GitHub": {"color": "181717", "logo": "github"},
        "Jira": {"color": "0052CC", "logo": "jira"},
    }
}

def generate_badge_url(label, color, logo, style="for-the-badge", logo_color="white"):
    """
    Generates a Shields.io URL.
    """
    # Shields.io format needs hyphens escaped or specific logic, but simplest is:
    # https://img.shields.io/badge/<Label>-<Color>?style=<style>&logo=<logo>&logoColor=<logoColor>
    # Note: Label spaces should be %20, but shields handles unencoded spaces sometimes. 
    # Best to replace spaces with %20.
    safe_label = label.replace(" ", "%20")
    safe_color = color.replace("#", "")
    return f"https://img.shields.io/badge/{safe_label}-{safe_color}?style={style}&logo={logo}&logoColor={logo_color}"

def generate_markdown(label, url, link=None):
    if link:
        return f"[![{label}]({url})]({link})"
    return f"![{label}]({url})"
