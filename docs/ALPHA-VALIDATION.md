# Alpha validation and evidence

## One-command verification

```bash
bash scripts/alpha-check.sh projects/alpha-corporate
```

يبني الموقع، يجدد index، يشغل البوابات، ثم 18 اختبار happy/negative.

## Studio/build gates

| الفاحص | الدليل |
| --- | --- |
| `manifest_schema_validate` | envelopes وcontent hashes لكل العقود |
| `truth_ledger_lint` | حدود الحقائق والموافقات |
| `content_lint` / `bilingual_parity_check` | بنية المحتوى وتطابق الحقائق |
| `site_contract_check` | strict JSON، routes، locale، blocks وCTA |
| `studio_contract_check` | strategy/creative/motion/providers/safety |
| `image_plan_check` / `asset_integrity_check` | الخطة وفك ترميز الصور وhash/budget |
| `video_asset_check` | FFprobe، MP4/WebM، الأبعاد، المدة، hash/budget |
| `contrast_audit` | التباين الحتمي وإحالة text-over-image للإنسان |
| `build_output_check` | routes، links، landmarks، assets ووزن CSS/JS |
| `seo_output_check` | canonical، hreflang، OG، JSON-LD وsitemap |
| security/privacy probes | secrets، headers، privacy وSCA |

## Negative proof

الاختبارات تثبت أيضاً أن المنظومة ترفض:

- صورة WebP مزيفة؛
- فيديو WebM فاسد؛
- JSON بمفتاح مكرر؛
- سر داخل generation plan؛
- loop فيديو 10 ثوانٍ غير مدعوم؛
- عقد أو route غير صالح.

وتثبت أن dry-run لا يحتاج مفتاحاً، وأن root routing يبني الصفحة الأساسية في `/`.

## Runtime browser matrix

Playwright مثبت في `package-lock.json` وCI يثبت Chromium لاختبار first-paint على AR/EN،
desktop/mobile، light/dark، no-JS وشروط فشل الصور. إذا لم يتوفر Chromium محلياً فذلك
`Cannot confirm locally` ولا يغير نجاح اختبارات build/decode.

## Human gates

لا يثبت أي Probe:

- ملاءمة الاتجاه الإبداعي أو درجة الإبهار؛
- صحة claim الواقعي خارج الوثيقة؛
- فصاحة العربية وموافقة العميل النهائية؛
- قابلية قراءة كل إطار فيديو؛
- الامتثال القانوني في الدولة؛
- Core Web Vitals في أجهزة الإنتاج؛
- نجاح حساب provider أو فوترة وحصة API.

هذه البنود تحتاج مراجعين وموافقة مالك وتجربة production.
