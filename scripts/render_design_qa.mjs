import {spawn} from "node:child_process";
import {createHash} from "node:crypto";
import {mkdtemp, mkdir, readFile, readdir, rm, writeFile} from "node:fs/promises";
import {tmpdir} from "node:os";
import {basename, join, resolve} from "node:path";
import {pathToFileURL} from "node:url";
import {setTimeout as delay} from "node:timers/promises";

const [, , output, ...inputs] = process.argv;
if (!output || !inputs.length) throw new Error("Usage: node scripts/render_design_qa.mjs OUTPUT HTML_FILE_OR_DIRECTORY ...");
const binary = process.env.CHROME_BIN ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const profile = await mkdtemp(join(tmpdir(), "design-mcp-qa-"));
const child = spawn(binary, ["--headless", "--disable-background-networking", "--disable-sync",
    "--disable-extensions", "--no-first-run", "--hide-scrollbars", "--no-default-browser-check",
    "--remote-debugging-port=0", `--user-data-dir=${profile}`, "about:blank"], {stdio: "ignore"});
const childExit = new Promise((done) => child.once("exit", done));
let socket;
let startupError;
child.once("error", (error) => { startupError = error; });
try {
    await mkdir(output, {recursive: true});
    let port;
    for (let attempt = 0; attempt < 100 && !port; attempt++) {
        try { port = (await readFile(join(profile, "DevToolsActivePort"), "utf8")).split("\n")[0]; }
        catch (error) {
            if (startupError) throw startupError;
            if (error.code !== "ENOENT") throw error;
            await delay(100);
        }
    }
    if (!port) throw new Error("Chrome did not start");
    const version = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json();
    const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
    socket = new WebSocket(targets.find((target) => target.type === "page").webSocketDebuggerUrl);
    await new Promise((done, fail) => {
        socket.addEventListener("open", done, {once: true});
        socket.addEventListener("error", fail, {once: true});
    });
    let sequence = 0;
    const calls = new Map();
    const events = new Map();
    socket.addEventListener("message", ({data}) => {
        const message = JSON.parse(data);
        if (message.id && calls.has(message.id)) {
            const callback = calls.get(message.id);
            calls.delete(message.id);
            callback(message);
        }
        if (message.method && events.has(message.method)) {
            events.get(message.method)(message.params);
            events.delete(message.method);
        }
    });
    function send(method, params = {}) {
        const id = ++sequence;
        return new Promise((done, fail) => {
            const timer = setTimeout(() => { calls.delete(id); fail(new Error(method + " timed out")); }, 12000);
            calls.set(id, (message) => {
                clearTimeout(timer);
                if (message.error) fail(new Error(JSON.stringify(message.error)));
                else done(message.result);
            });
            socket.send(JSON.stringify({id, method, params}));
        });
    }
    function listen(method) {
        return new Promise((done, fail) => {
            const timer = setTimeout(() => { events.delete(method); fail(new Error(method + " timed out")); }, 15000);
            events.set(method, (value) => { clearTimeout(timer); done(value); });
        });
    }
    await send("Page.enable");
    const paths = [];
    for (const input of inputs) {
        if (input.endsWith(".html")) paths.push(input);
        else {
            const entries = await readdir(input);
            paths.push(...entries.filter((entry) => entry.endsWith(".html")).sort().map((entry) => join(input, entry)));
        }
    }
    const report = {browser: version.Browser, captures: []};
    for (const input of paths) {
        const content = await readFile(input);
        for (const width of [1440, 390]) {
            const height = width === 1440 ? 920 : 844;
            await send("Emulation.setDeviceMetricsOverride", {width, height, deviceScaleFactor: 1, mobile: false});
            await send("Emulation.setEmulatedMedia", {features: [{name: "prefers-reduced-motion", value: "reduce"}]});
            const loaded = listen("Page.loadEventFired");
            const navigation = await send("Page.navigate", {url: pathToFileURL(resolve(input)).href});
            if (navigation.errorText) throw new Error(navigation.errorText);
            await loaded;
            const {result, exceptionDetails} = await send("Runtime.evaluate", {
                expression: `(async () => {
                    await Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 2500))]);
                    const h = document.querySelector('h1');
                    const body = getComputedStyle(document.body);
                    const heading = h && getComputedStyle(h);
                    const main = document.querySelector('main');
                    const action = main?.querySelector('[data-qa-action],button:not([disabled]),a[href]') ?? null;
                    const before = action?.getBoundingClientRect();
                    const sections = [...document.querySelectorAll("main > section, main > article")];
                    const geometry = sections.map(section => {
                        const rect = section.getBoundingClientRect();
                        const style = getComputedStyle(section);
                        return {x: Math.round(rect.x), width: Math.round(rect.width),
                            align: style.textAlign, padding: style.paddingTop};
                    });
                    return {title: document.title, documentWidth: document.documentElement.scrollWidth,
                        overflow: document.documentElement.scrollWidth > innerWidth + 1,
                        heading: h?.textContent?.trim(), headlinePx: heading && parseFloat(heading.fontSize),
                        headingFont: heading?.fontFamily, bodyFont: body.fontFamily,
                        ink: body.color, paper: body.backgroundColor, geometry,
                        fontFaces: [...document.fonts].map(face => [face.family, face.status]),
                        bodyPx: parseFloat(body.fontSize), headingAlignment: heading?.textAlign,
                        action: action?.textContent?.trim(), actionInViewport: !!before && before.bottom <= innerHeight,
                        landmarkCount: document.querySelectorAll('main').length,
                        links: document.querySelectorAll('a[href]').length, buttons: document.querySelectorAll('button').length};
                })()`, awaitPromise: true, returnByValue: true
            });
            if (exceptionDetails) throw new Error(JSON.stringify(exceptionDetails));
            const {data} = await send("Page.captureScreenshot", {format: "png"});
            const screenshot = Buffer.from(data, "base64");
            await send("Runtime.evaluate", {expression: "document.documentElement.style.filter='blur(8px) grayscale(1)'"});
            const blurred = await send("Page.captureScreenshot", {format: "png"});
            await send("Runtime.evaluate", {expression: "document.documentElement.style.removeProperty('filter')"});
            const name = `${basename(input, ".html")}-${width}.png`;
            await writeFile(join(output, name), screenshot);
            const blurName = name.replace(".png", "-blur.png");
            await writeFile(join(output, blurName), Buffer.from(blurred.data, "base64"));
            report.captures.push({file: input, width, height, screenshot: name, squint: blurName,
                sourceSha256: createHash("sha256").update(content).digest("hex"),
                imageSha256: createHash("sha256").update(screenshot).digest("hex"), ...result.value});
        }
    }
    await writeFile(join(output, "report.json"), JSON.stringify(report, null, 2) + "\n");
    console.log(`${report.captures.length} captures`);
} finally {
    socket?.close();
    child.kill("SIGTERM");
    if (child.pid) await childExit;
    await rm(profile, {recursive: true, force: true});
}
