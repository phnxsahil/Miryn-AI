import os

files_to_update = [
    r"d:\Projects\MirynAI-Production\Miryn-AI\miryn\frontend\public\landing\index.html",
    r"d:\Projects\MirynAI-Production\framer-landing-page\index.html"
]

for file_path in files_to_update:
    if not os.path.exists(file_path):
        continue
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add Documentation click interceptor
    interceptor_needle = "txt === 'Get Started' ||"
    interceptor_replacement = "txt === 'Documentation' || txt === 'Docs' ? (function(){ var u = '/docs'; if (window.top && window.top !== window) { window.top.location.href = u; } else { window.location.href = u; } return false; })() : txt === 'Get Started' ||"
    
    if interceptor_needle in content and "txt === 'Documentation'" not in content:
        content = content.replace(interceptor_needle, interceptor_replacement, 1)

    # 2. Add Documentation in footer Pages section right before Insights or after Privacy Policy
    footer_needle = 'href="./blog">Insights</a><!--/$--></p></div><div class="framer-u86jjt"'
    doc_link = '<div class="framer-docs-container"><div class="framer-ViOqW framer-MWEtl framer-FoaEz framer-1dxi3gq framer-v-1dxi3gq" data-framer-name="Default" data-highlight="true" tabindex="0" style="height:100%"><div class="framer-o7748u" data-framer-component-type="RichTextContainer" style="transform:none"><p class="framer-text framer-styles-preset-p11uu0" data-styles-preset="ic733n7x0"><!--$--><a class="framer-text framer-styles-preset-gv2o4p" data-styles-preset="hQQzlC7Yp" href="/docs" target="_top">Documentation</a><!--/$--></p></div><div class="framer-u86jjt" style="background-color:var(--token-35958b5f-fcd4-4988-a517-708c39eda844, rgb(250, 250, 250));transform:scale(0)"></div></div></div>'
    
    if footer_needle in content and 'href="/docs"' not in content:
        # Insert before Insights
        content = content.replace(footer_needle, footer_needle + doc_link, 1)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated docs link in:", file_path)
