// Renders emoji icons with AppKit (Apple Color Emoji) - no third-party dependency.
// Usage: osascript -l JavaScript render_icons.js <jobs.json> <output dir> <size> <padding>
// jobs.json : [{"emoji": "😀", "file": "grinning face.png"}, ...]
// stdout    : JSON array with the files that could not be rendered.

ObjC.import("AppKit");
ObjC.import("Foundation");

function run(argv) {
  const jobs = JSON.parse(ObjC.unwrap(
    $.NSString.stringWithContentsOfFileEncodingError(argv[0], $.NSUTF8StringEncoding, $())));
  const outDir = argv[1];
  const size = parseInt(argv[2], 10);
  const padding = parseInt(argv[3], 10);
  const canvas = size + padding;
  const failed = [];

  $.NSApplication.sharedApplication;
  const probeFont = $.NSFont.fontWithNameSize("Apple Color Emoji", size);
  const probeAttrs = $.NSDictionary.dictionaryWithObjectForKey(probeFont, $.NSFontAttributeName);
  // An unsupported ZWJ sequence is drawn as several glyphs: much wider than a single emoji.
  const maxWidth = $.NSString.alloc.initWithUTF8String("😀").sizeWithAttributes(probeAttrs).width * 1.6;

  for (const job of jobs) {
    try {
      const text = $.NSString.alloc.initWithUTF8String(job.emoji);
      const measure = text.sizeWithAttributes(probeAttrs);
      if (measure.width > maxWidth) { failed.push(job.file); continue; }
      // Fit the glyph in size x size, whatever its natural advance is.
      const scale = Math.min(1, size / Math.max(measure.width, measure.height));
      const font = $.NSFont.fontWithNameSize("Apple Color Emoji", size * scale);
      const attrs = $.NSDictionary.dictionaryWithObjectForKey(font, $.NSFontAttributeName);
      const box = text.sizeWithAttributes(attrs);

      const rep = $.NSBitmapImageRep.alloc.initWithBitmapDataPlanesPixelsWidePixelsHighBitsPerSampleSamplesPerPixelHasAlphaIsPlanarColorSpaceNameBytesPerRowBitsPerPixel(
        $(), canvas, canvas, 8, 4, true, false, $.NSDeviceRGBColorSpace, 0, 0);
      const context = $.NSGraphicsContext.graphicsContextWithBitmapImageRep(rep);
      $.NSGraphicsContext.saveGraphicsState;
      $.NSGraphicsContext.setCurrentContext(context);
      text.drawAtPointWithAttributes(
        $.NSMakePoint((canvas - box.width) / 2, (canvas - box.height) / 2), attrs);
      context.flushGraphics;
      $.NSGraphicsContext.restoreGraphicsState;

      const png = rep.representationUsingTypeProperties($.NSBitmapImageFileTypePNG, $.NSDictionary.dictionary);
      if (!png.writeToFileAtomically(outDir + "/" + job.file, true)) { failed.push(job.file); }
    } catch (error) {
      failed.push(job.file);
    }
  }
  return JSON.stringify(failed);
}
