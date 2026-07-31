# Media providers and execution boundary

## Provider configuration

| الاستخدام | العقد المرجعي | متغير البيئة | التنفيذ |
| --- | --- | --- | --- |
| Still / key image | OpenAI GPT Image 2 snapshot configured in `generation-plan.json` | `OPENAI_API_KEY` | Images API |
| Image-to-video hero | Luma Ray 3.2 configured in `generation-plan.json` | `LUMA_AGENTS_API_KEY` | Luma Agents generations API |
| Web finishing | FFmpeg/FFprobe محلي | لا يوجد | MP4 + WebM + WebP poster |

النماذج ليست hard-coded في تجربة الصفحة؛ `generation-plan.json` يحدد provider/model،
بينما adapter يتحقق من شكل الطلب. تغيّر نموذج provider يحتاج تحديث الخطة والاختبارات.

## حدود الأمان والتكلفة

- أوامر image/video هي dry-run ما لم يُضف `--execute`.
- dry-run لا يقرأ المفتاح ولا يرسل طلباً.
- `--execute` قد ينشئ تكلفة خارجية ويحتاج موافقة المشغل.
- لا تسجل المفاتيح في JSON أو job evidence أو Git أو ZIP.
- `generation-jobs.jsonl` يسجل provider، model، slot، prompt version وgeneration id فقط.
- التوليد مسموح للـconceptual slots؛ documentary assets يجب أن تأتي من المصدر الحقيقي.
- فيديو الهيرو لا يبدأ قبل اعتماد still بشرياً.

## دورة الفيديو

1. يعتمد الـCreative Director والعميل still frame.
2. `media_pipeline.py video` يبني payload من `video-manifest.json`.
3. `--execute --wait` يرسل job، يتابع حالته وينزّل الملف المؤقت فور اكتماله.
4. `transcode` ينتج MP4 وWebM وPoster لكل من desktop/mobile.
5. عند تمرير `--slot` و`--rendition` يحدّث manifest بالمسارات وSHA-256 ويختمه.
6. `video_asset_check.py` يفك ترميز كل ملف ويقارن الأبعاد والمدة والميزانية.
7. الواجهة تعرض poster أولاً؛ لا يظهر الفيديو حتى يقرأ بياناته ويبدأ التشغيل.

## قيود مرجع Ray 3.2 في هذه النسخة

الـadapter يقبل 5 أو 10 ثوانٍ، لكن seamless `loop=true` محصور في 5 ثوانٍ. الدقة
مقيدة إلى `360p`, `540p`, `720p`, أو `1080p`، والنسب إلى القيم المعلنة في
`studio/providers.py`. فشل provider لا يغيّر Build الموجود؛ تبقى الصورة الثابتة صالحة.

## ما تم التحقق منه في الحزمة

تم اختبار payload builders، dry-run بلا مفاتيح، حظر loop غير صالح، فك ترميز MP4/WebM،
hashes، الأبعاد، المدة والميزانية. لم تُستخدم مفاتيح حسابات خارجية ولم يُنفذ طلب مدفوع؛
نجاح الحساب والفوترة والحصص لا يمكن تأكيده قبل إعداد مفاتيح المشغّل.
