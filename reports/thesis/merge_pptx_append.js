const fs = require("fs");
const path = require("path");
const JSZip = require("C:/Users/shanu/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/jszip");

const root = path.resolve(__dirname);
const sourcePptx = "C:/Users/shanu/Downloads/BTECH-86_24th (1).pptx";
const appendPptx = path.join(root, "BTECH-86_24th_extended_newslides.pptx");
const outputPptx = path.join(root, "BTECH-86_24th_Final_Extended.pptx");

function text(file) {
  return file.async("string");
}

function buf(file) {
  return file.async("nodebuffer");
}

function maxMatch(names, regex) {
  let max = 0;
  for (const n of names) {
    const m = n.match(regex);
    if (m) max = Math.max(max, Number(m[1]));
  }
  return max;
}

async function main() {
  const srcZip = await JSZip.loadAsync(fs.readFileSync(sourcePptx));
  const extZip = await JSZip.loadAsync(fs.readFileSync(appendPptx));

  const srcNames = Object.keys(srcZip.files);
  const extNames = Object.keys(extZip.files);

  const srcSlideCount = maxMatch(srcNames, /^ppt\/slides\/slide(\d+)\.xml$/);
  const extSlideCount = maxMatch(extNames, /^ppt\/slides\/slide(\d+)\.xml$/);
  const srcMediaMax = maxMatch(srcNames, /^ppt\/media\/image(\d+)\./);

  let nextMedia = srcMediaMax + 1;
  let relCounter = 0;

  const presXml = await text(srcZip.file("ppt/presentation.xml"));
  const presRelsXml = await text(srcZip.file("ppt/_rels/presentation.xml.rels"));
  const contentTypesXml = await text(srcZip.file("[Content_Types].xml"));

  const existingRelIds = [...presRelsXml.matchAll(/Id="rId(\d+)"/g)].map((m) => Number(m[1]));
  relCounter = Math.max(...existingRelIds, 1) + 1;
  const existingSlideIds = [...presXml.matchAll(/<p:sldId id="(\d+)"/g)].map((m) => Number(m[1]));
  let nextSlideId = Math.max(...existingSlideIds, 255) + 1;

  let newPresXml = presXml;
  let newPresRelsXml = presRelsXml;
  let newContentTypesXml = contentTypesXml;

  for (let i = 1; i <= extSlideCount; i++) {
    const newSlideNum = srcSlideCount + i;
    const slidePath = `ppt/slides/slide${i}.xml`;
    const slideRelPath = `ppt/slides/_rels/slide${i}.xml.rels`;
    const srcSlideXml = await text(extZip.file(slidePath));
    let srcRelXml = extZip.file(slideRelPath) ? await text(extZip.file(slideRelPath)) : null;

    if (srcRelXml) {
      const mediaTargets = [...srcRelXml.matchAll(/Target="\.\.\/media\/([^"]+)"/g)].map((m) => m[1]);
      for (const mediaName of mediaTargets) {
        const ext = path.extname(mediaName);
        const newMediaName = `image${nextMedia++}${ext}`;
        const mediaBuf = await buf(extZip.file(`ppt/media/${mediaName}`));
        srcZip.file(`ppt/media/${newMediaName}`, mediaBuf);
        srcRelXml = srcRelXml.replace(new RegExp(`\\.\\./media/${mediaName.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`, "g"), `../media/${newMediaName}`);
      }
      srcZip.file(`ppt/slides/_rels/slide${newSlideNum}.xml.rels`, srcRelXml);
    }

    srcZip.file(`ppt/slides/slide${newSlideNum}.xml`, srcSlideXml);

    const newRid = `rId${relCounter++}`;
    const relNode = `<Relationship Id="${newRid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide${newSlideNum}.xml"/>`;
    newPresRelsXml = newPresRelsXml.replace("</Relationships>", `${relNode}</Relationships>`);

    const slideNode = `<p:sldId id="${nextSlideId++}" r:id="${newRid}"/>`;
    newPresXml = newPresXml.replace("</p:sldIdLst>", `${slideNode}</p:sldIdLst>`);

    const overrideNode = `<Override PartName="/ppt/slides/slide${newSlideNum}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>`;
    newContentTypesXml = newContentTypesXml.replace("</Types>", `${overrideNode}</Types>`);
  }

  srcZip.file("ppt/presentation.xml", newPresXml);
  srcZip.file("ppt/_rels/presentation.xml.rels", newPresRelsXml);
  srcZip.file("[Content_Types].xml", newContentTypesXml);

  const outBuf = await srcZip.generateAsync({ type: "nodebuffer" });
  fs.writeFileSync(outputPptx, outBuf);
  console.log(outputPptx);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
