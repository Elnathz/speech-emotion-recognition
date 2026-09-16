import { chromium } from "playwright";

const streamlitUrl =
  process.env.STREAMLIT_URL ?? "https://emotionrecognitionspeech.streamlit.app/";

const browser = await chromium.launch({
  headless: true,
});

const page = await browser.newPage();

try {
  console.log(`[CHECK] Membuka ${streamlitUrl}`);

  await page.goto(streamlitUrl, {
    waitUntil: "domcontentloaded",
    timeout: 120000,
  });

  const streamlitFrameElement = page.locator('iframe[title="streamlitApp"]');
  await streamlitFrameElement.waitFor({ state: "visible", timeout: 120000 });

  const streamlitFrame = page.frameLocator('iframe[title="streamlitApp"]');
  const wakeButton = streamlitFrame.getByRole("button", {
    name: /yes, get this app back up|wake/i,
  });

  if (await wakeButton.count()) {
    console.log("[WAKE] Menekan tombol untuk membangunkan aplikasi");
    await wakeButton.first().click();
  }

  await streamlitFrame
    .locator('[data-testid="stAppViewContainer"]')
    .waitFor({ state: "visible", timeout: 90000 });

  console.log(`[OK] Streamlit aktif di ${page.url()}`);
  console.log(`[CHECK] Judul halaman: ${await page.title()}`);
} finally {
  await browser.close();
}
