"""LaTeX to Markdown converter — extracts structured content from .tex files."""
import re
import os


def latex_to_markdown(filepath: str) -> str:
    """Convert LaTeX file to markdown text."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    lines = []
    # Strip preamble
    begin_doc = content.find(r"\begin{document}")
    end_doc = content.find(r"\end{document}")
    if begin_doc >= 0:
        content = content[begin_doc + len(r"\begin{document}"):]
    if end_doc >= 0:
        content = content[:end_doc]

    # Convert sections
    content = re.sub(r'\\section\*?\{(.+?)\}', r'# \1', content)
    content = re.sub(r'\\subsection\*?\{(.+?)\}', r'## \1', content)
    content = re.sub(r'\\subsubsection\*?\{(.+?)\}', r'### \1', content)

    # Convert formatting
    content = re.sub(r'\\textbf\{(.+?)\}', r'**\1**', content)
    content = re.sub(r'\\textit\{(.+?)\}', r'*\1*', content)
    content = re.sub(r'\\texttt\{(.+?)\}', r'`\1`', content)

    # Convert lists
    content = re.sub(r'\\begin\{itemize\}', '', content)
    content = re.sub(r'\\end\{itemize\}', '', content)
    content = re.sub(r'\\begin\{enumerate\}', '', content)
    content = re.sub(r'\\end\{enumerate\}', '', content)
    content = re.sub(r'\\item\s', '- ', content)

    # Remove common LaTeX commands
    content = re.sub(r'\\title\{(.+?)\}', r'# \1\n', content)
    content = re.sub(r'\\author\{(.+?)\}', r'**作者:** \1\n', content)
    content = re.sub(r'\\date\{(.+?)\}', r'*日期: \1*\n', content)
    content = re.sub(r'\\maketitle', '', content)
    content = re.sub(r'\\tableofcontents', '', content)
    content = re.sub(r'\\label\{[^}]*\}', '', content)
    content = re.sub(r'\\ref\{[^}]*\}', '', content)
    content = re.sub(r'\\cite\{[^}]*\}', '[citation]', content)
    content = re.sub(r'\\hline', '---', content)
    content = re.sub(r'\\newpage', '\n---\n', content)
    content = re.sub(r'\\vspace\{[^}]*\}', '', content)
    content = re.sub(r'\\hspace\{[^}]*\}', '', content)

    # Clean up
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = content.strip()

    return content
