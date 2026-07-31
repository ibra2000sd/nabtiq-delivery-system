# Nabtiq Studio Alpha 3.1

منظومة تشغيل داخلية لبناء مواقع **Corporate/Brochure** عربية–إنجليزية من ملفات العميل
إلى Build ثابت قابل للتسليم. تعمل من سطر الأوامر أو داخل Claude Code، وتحفظ الاستراتيجية
والمحتوى والاتجاه الإبداعي والوسائط والحركة كعقود قابلة للفحص وإعادة البناء.

هذه نسخة **Functional Internal Alpha** وليست SaaS عامة أو محرراً بصرياً.

## ما أصبح وظيفياً

- أربع صفحات منطقية تُبنى إلى ثمانية مسارات AR/EN مع RTL/LTR بنيوي.
- اختيار لغة على `/` أو وضع اللغة الأساسية مباشرة على جذر الدومين.
- استقبال ملفات العميل وفهرسة DOCX/PDF والنصوص مع SHA-256.
- زاحف HTTPS اختياري، محدود وعلى نفس النطاق، مع dry-run ومراعاة `robots.txt`.
- عقود استراتيجية، اتجاه إبداعي، Copy ثنائي اللغة، SEO، Design Tokens وحركة.
- أربعة مستويات زجاج دلالية: nav، surface، deep وluminous مع بديل معتم.
- Hero سينمائي متجاوب: صورة معتمدة أولاً، ثم WebM/MP4 عند السماح بالحركة.
- بديل Poster وإيقاف الفيديو والحركة عند `prefers-reduced-motion`.
- مكوّنات: Cards، Metrics، Split، Steps، Route story، FAQ، Gallery،
  Before/After، Logo cloud، Contact، Lead form وCTA.
- موصل GPT Image 2 للصور وLuma Ray 3.2 للفيديو، بحد تنفيذ صريح.
- Build ثابت حتمي، عقود مختومة، فحص صور وفيديو حقيقي، SEO وروابط وميزانيات.

مشروع `projects/alpha-corporate` شركة خيالية ومرجع تنفيذي، وليس محتوى صالحاً للنشر لعميل.

## التحقق

المتطلبات: Python 3.12، FFmpeg/FFprobe، وPillow.

```bash
python3 -m pip install -r requirements-dev.txt
make alpha-check
```

النتيجة المرجعية: 17 بوابة Build و18 اختباراً، ثم Build من ثمانية مسارات في
`projects/alpha-corporate/build/`.

للمعاينة:

```bash
make alpha
python3 -m http.server 8080 --directory projects/alpha-corporate/build
```

افتح `http://localhost:8080/en/` أو `http://localhost:8080/ar/`.

## بدء عميل جديد

```bash
python3 scripts/new_project.py client-name \
  --brand-en "Client Name" \
  --brand-ar "اسم العميل" \
  --website "https://www.example.com" \
  --email "hello@example.com" \
  --default-locale ar \
  --routing default-locale-root
```

الأمر ينشئ المشروع ويختم عقوده ويبنيه. المحتوى والوسائط المنسوخة من المرجع placeholders
ويجب استبدالها واعتمادها. داخل Claude Code استخدم عبارة مثل:

> استخدم مهارة studio-delivery لبناء موقع هذا العميل. ابدأ باستقبال الملفات وسجل الحقيقة،
> ولا تنفذ أي توليد مدفوع أو نشر أو DNS من دون موافقتي الصريحة.

## استقبال الملفات والموقع الحالي

```bash
python3 scripts/intake_files.py projects/client-name /path/to/client-files

python3 scripts/crawl_site.py projects/client-name https://www.example.com
# بعد فحص خطة dry-run والموافقة على الشبكة:
python3 scripts/crawl_site.py projects/client-name https://www.example.com --execute
```

الأول يكتب `source-inventory.json`. الثاني يكتب `current-site-inventory.json` ولا يخرج
عن النطاق الأصلي.

## إنتاج الصور والفيديو

الأوامر افتراضياً dry-run: لا تقرأ مفتاحاً ولا ترسل طلباً ولا تنشئ تكلفة.

```bash
python3 scripts/media_pipeline.py image projects/client-name home.hero
python3 scripts/media_pipeline.py video projects/client-name home.hero.motion
```

بعد اعتماد الاتجاه الإبداعي والـstill، وبموافقة المشغّل:

```bash
export OPENAI_API_KEY="..."
export LUMA_AGENTS_API_KEY="..."

python3 scripts/media_pipeline.py image projects/client-name home.hero --execute
python3 scripts/media_pipeline.py video projects/client-name home.hero.motion --execute --wait
```

القيم لا تدخل ملفات المشروع. بعد تنزيل فيديو مصدر:

```bash
python3 scripts/media_pipeline.py transcode projects/client-name projects/client-name/assets/source/hero-luma.mp4 \
  --prefix hero-loop-desktop --width 1280 --height 720 \
  --slot home.hero.motion --rendition desktop
```

ينتج MP4 وWebM وPoster، يحدّث hashes في manifest ويعيد ختمه.

## ذاكرة المشروع

| العقد | المسؤولية |
| --- | --- |
| `source-inventory.json` | ملفات العميل، hashes، مقتطفات وحالة المراجعة |
| `current-site-inventory.json` | صفحات الموقع الحالي قبل الاستبدال |
| `truth-ledger.json` | الحقائق، الأدلة وموقف النشر |
| `site-strategy.json` | الجمهور والتموضع والمبادئ |
| `site-map.json` | الصفحات، AR/EN وسياسة الروابط |
| `pages/*.content.json` | Copy وSEO ومكوّنات الصفحات |
| `creative-direction.json` | الفكرة الفنية والهيرو وحدود المواد |
| `design-tokens.json` | الألوان والخط والمسافات والزجاج والحركة |
| `image-manifest.json` | خطة الصور والقصّ والبدائل والمصدر |
| `motion-spec.json` | غرض كل حركة وبديل reduced-motion |
| `generation-plan.json` | المزود والنموذج وأسماء متغيرات البيئة |
| `video-manifest.json` | الفيديو، Start frame، poster، المصادر والميزانية |

## الحدود الصادقة

موجود: مسار تشغيل داخلي كامل، موصلات توليد حقيقية، Build بصري متقدم، وحواجز قابلة للتكرار.

غير موجود: واجهة عميل، تسجيل دخول، قاعدة بيانات، tenancy، billing، محرر سحب وإفلات،
نشر تلقائي، DNS تلقائي، أو ضمان جودة جمالية/لغوية من دون مراجعة بشرية. موصلات API
تحتاج حسابات صالحة ومفاتيح لدى المشغّل؛ الحزمة لا تتضمن مفاتيح ولم تُجرِ طلباً مدفوعاً.

راجع `docs/STUDIO-WORKFLOW.md` و`docs/MEDIA-PROVIDERS.md` و
`docs/ALPHA-VALIDATION.md`.
