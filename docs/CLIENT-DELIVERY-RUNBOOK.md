# دليل تسليم عميل

## 0. افتح المشروع

افتح المستودع في Claude Code واطلب استخدام `studio-delivery`. أنشئ المشروع عبر
`scripts/new_project.py` مع الاسمين والدومين والبريد وسياسة اللغة. الناتج scaffold فقط.

## 1. استقبل المصادر

شغّل `intake_files.py` على نسخة ملفات العميل. عند استبدال موقع قائم شغّل crawler dry-run،
ثم اطلب الإذن قبل `--execute`. لا تنقل claim من الموقع القديم بلا إثبات.

## 2. الحقيقة والاستراتيجية

استخرج كل claim إلى `truth-ledger.json`. المفقود سؤال blocking، وليس تخميناً. بعد المراجعة
اكتب `site-strategy.json` و`site-map.json`. وافق العميل على الجمهور، الرسالة، الصفحات وCTA.

## 3. Copy ثنائي اللغة

اكتب اللغة الأساسية طبيعياً ثم adapt اللغة الأخرى، مع نفس `claim_refs`. اطلب مراجعة مستقلة
للعربية والإنجليزية. شغّل content وparity gates.

## 4. Creative direction ونظام التصميم

قدم 2–3 اتجاهات قصيرة؛ يعتمد العميل واحداً فقط. سجله في `creative-direction.json`.
ابنِ tokens دلالية تتضمن أربعة glass depths، ثم image manifest بمكوّن desktop/mobile منفصل.
لا تولد media قبل اعتماد الاتجاه والـstill.

## 5. الحركة والوسائط

سجل كل حركة في `motion-spec.json`: intent، trigger، properties، duration، easing وبديل
reduced-motion. أنشئ `generation-plan.json` و`video-manifest.json`.

شغّل media dry-run. بعد إذن صريح فقط ضع المفاتيح في البيئة وشغّل `--execute`. استخدم
FFmpeg finishing، حدّث hashes، ثم شغّل مراجعي الإخراج والحركة.

## 6. البناء والتحقق

```bash
python3 scripts/build_site.py projects/<slug>
bash scripts/run-checks.sh projects/<slug> build
```

أصلح كل BLOCKED/FAIL. نفذ visual QA على الجوال والمكتب، AR/EN، light/dark،
normal/reduced-motion وno-JS. جودة “wow” وموافقة المحتوى قرار بشري.

## 7. الهجرة والنشر

اعتمد redirect map، endpoint النماذج، analytics/privacy، مالك DNS وrollback. سجل
deployment authorization من owner/release-manager. Workflow النشر الحالي يحتاج ربطاً
فعلياً بالمضيف؛ لا تغيّر DNS أو تدّعي monitoring قبل تنفيذ هذا الربط والتحقق من الرابط الحي.

## التسليم

سلّم `build/` للنشر، وبقية `projects/<slug>/` كذاكرة المشروع: المصادر المفهرسة،
العقود، manifests، evidence والموافقات. لا تسلّم `.env` أو أي API key.
