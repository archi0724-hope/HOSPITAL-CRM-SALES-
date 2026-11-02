"""Build the single-file offline frontend with Python's standard library."""
from pathlib import Path
import base64
root=Path(__file__).resolve().parent
logo='data:image/png;base64,'+base64.b64encode((root/'assets/hope-logo.png').read_bytes()).decode('ascii')
html=(root/'index.html').read_text(encoding='utf-8')
html=html.replace('<link rel="stylesheet" href="styles.css">','<style>\n'+(root/'styles.css').read_text(encoding='utf-8')+'\n</style>')
html=html.replace('<link rel="stylesheet" href="operations.css">','<style>\n'+(root/'operations.css').read_text(encoding='utf-8')+'\n</style>')
html=html.replace('<link rel="stylesheet" href="sections.css">','<style>\n'+(root/'sections.css').read_text(encoding='utf-8')+'\n</style>')
html=html.replace('<link rel="stylesheet" href="assistant.css">','<style>\n'+(root/'assistant.css').read_text(encoding='utf-8')+'\n</style>')
html=html.replace('<link rel="stylesheet" href="/static/font-size.css">','<style>\n'+(root/'sales-ops/static/font-size.css').read_text(encoding='utf-8')+'\n</style>')
html=html.replace('<script src="/static/font-size.js"></script>','<script>\n'+(root/'sales-ops/static/font-size.js').read_text(encoding='utf-8').replace('</script','<\\/script')+'\n</script>')
for filename in ('data.js','excel.js','sales-report.js','operations.js','app.js'):
    script=(root/filename).read_text(encoding='utf-8').replace('assets/hope-logo.png',logo).replace('</script','<\\/script')
    html=html.replace('<script src="'+filename+'"></script>','<script>\n'+script+'\n</script>')
html=html.replace('assets/hope-logo.png',logo)
(root/'HOSPkart_CRM_Standalone.html').write_text(html,encoding='utf-8')
print('Created HOSPkart_CRM_Standalone.html')
