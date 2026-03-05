"""Download Dribbble images from pre-collected CDN URLs."""
import httpx
import hashlib
import time
import re
from pathlib import Path
from html import unescape

SCREENSHOT_DIR = Path(__file__).parent.parent / "screenshots" / "dribbble"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

# URLs collected via browser automation from Dribbble popular pages
RAW_URLS = """
https://cdn.dribbble.com/userupload/46948245/file/still-faa9709c192f3a54a13df5374a182b2a.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46946335/file/42039b2239ce8dd105e219fb8e61bb87.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46542405/file/still-ca3a7007342730ab6c4a2426bd2ffe7a.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46941953/file/still-f8f6b75852b3f8d669027b97ea8f188d.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46917594/file/3fae18fb2d277ce9fa0773c26267b1e5.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46958233/file/9584df3d069a1d7531f8b9c4ce4f7e7d.jpg?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46949997/file/still-8239e8f15befbedb9358bcfbadf40b43.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46953074/file/965e58a1530ca7dd66607f72414812ff.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46957372/file/ada5faef187038acf8a2a7f29f42b9ed.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/45749262/file/c8faf19961d991e73487b10351a03400.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46948240/file/4cc39afa5ae8c26677ae28adb97fa10c.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46945147/file/a3efd016e2ad13bbfc23200ced60998c.jpg?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46949266/file/c5ff50c18cbdad47a3b8ef47c630cf3a.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46952451/file/2373c8db5ecae2ba395394e30c9b15d1.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46945303/file/3c629595f63b34eeb0ddc10e06434c3c.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46949808/file/still-3b803f0a18b88027b1404a274ec25401.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46950049/file/a0a41aa240ec8d453b85e9a3d8ca7c6a.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46945259/file/59effbc8013048d19968adb6bdbf4909.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46952313/file/776978ed19f02a21c91dbf3071b0a8df.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46952426/file/9e35b67eee132a3e56042dd1e20eae24.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46944355/file/b6d03e3104407d9ff148eb4e1618e4b4.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46948685/file/56de7fbca4ab31630b2c0cdefa3a4767.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46949894/file/b7d12d3e8271ed75be5140bc97bff4b5.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46956181/file/2904d51100399d4f53702e7c2a031f80.png?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46956675/file/45db042dfd952599ba2f5b9ee7322776.jpg?format=webp&resize=1600x&vertical=center
https://cdn.dribbble.com/userupload/46954952/file/5bbfd3eb9379933c698b0980621d7efc.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46948242/file/2f377677b329d97259aaee425f388f52.png?resize=1600x
https://cdn.dribbble.com/userupload/46918384/file/d0fca486081115a4dc30a4688916b4d4.png?resize=1600x
https://cdn.dribbble.com/userupload/46927669/file/120c52fdf374765adb0cc42402486487.png?resize=1600x
https://cdn.dribbble.com/userupload/46943909/file/a438d70ea666f7c9c6dce6ffc71b8b45.png?resize=1600x
https://cdn.dribbble.com/userupload/46945008/file/25633bd2d5fba1fd1dc1bccd67fb3655.png?resize=1600x
https://cdn.dribbble.com/userupload/46949915/file/5e15c4ef4a2afc2f0bbc4c6bfd75e99d.png?resize=1600x
https://cdn.dribbble.com/userupload/46949770/file/139ac7b4b4ac873b5510941b1b931a7c.png?resize=1600x
https://cdn.dribbble.com/userupload/46952017/file/1faf3123711757c174a41663948d58b9.png?resize=1600x
https://cdn.dribbble.com/userupload/46950735/file/7babb6ce9c965871c8de027510eff538.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46949972/file/7daa5082b7d074e3fa75e0362c7e24b7.png?resize=1600x
https://cdn.dribbble.com/userupload/46945199/file/still-4ebe6954c4be88a4671595f06f41091e.png?resize=1600x
https://cdn.dribbble.com/userupload/46948868/file/74aacd7f609dd04536526cb7b7e03b24.png?resize=1600x
https://cdn.dribbble.com/userupload/46950775/file/4ef8f3c732fc3d7fb67ed62a4a601a85.png?resize=1600x
https://cdn.dribbble.com/userupload/46953718/file/fd652584c25de8f716b4458a6fe44b7a.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46952406/file/e5906d152b3f27e579aec6a5b9a46b8b.png?resize=1600x
https://cdn.dribbble.com/userupload/46950788/file/7de1691e1386d20b525cbb273dee28ae.png?resize=1600x
https://cdn.dribbble.com/userupload/46940494/file/bcb267a7852a2d4807006ef7d8438648.png?resize=1600x
https://cdn.dribbble.com/userupload/46945503/file/6afc8a9c1477641b00d00eb974950de3.png?resize=1600x
https://cdn.dribbble.com/userupload/46957342/file/still-ea558578a17ae6a21e93bfd731afc732.png?resize=1600x
https://cdn.dribbble.com/userupload/46941599/file/still-794bf24b197d3e65e1e1d1dfe76ad3bb.png?resize=1600x
https://cdn.dribbble.com/userupload/46932029/file/c761a66769e1b3adac8278cc60411122.png?resize=1600x
https://cdn.dribbble.com/userupload/46949620/file/still-196a79965bb79d50a7e408f8815bc06c.png?resize=1600x
https://cdn.dribbble.com/userupload/46956507/file/still-bd6d1db76da2820a8c817b638857c370.png?resize=1600x
https://cdn.dribbble.com/userupload/46917116/file/e66482de7821404b71ff9efe0e202766.png?resize=1600x
https://cdn.dribbble.com/userupload/46940883/file/120aa867f8caca8addb0a68a68ad4d84.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46936854/file/7418ae91812f965158cd64a6d929af99.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46957621/file/still-236194f4a8edb264d05e074517ac6f75.png?resize=1600x
https://cdn.dribbble.com/userupload/46950765/file/a4e2d91220f11f96e993403b9b1dd146.png?resize=1600x
https://cdn.dribbble.com/userupload/46958477/file/c6c126e65b9328e6b6dd07501ff7ba2c.png?resize=1600x
https://cdn.dribbble.com/userupload/46941886/file/1ea557c24e4dbd251d686917cdc66c36.png?resize=1600x
https://cdn.dribbble.com/userupload/46957495/file/f85928a17498199665dd7eacfd8302b6.png?resize=1600x
https://cdn.dribbble.com/userupload/46952822/file/6680140e8026e305f29b3f7884f2b584.png?resize=1600x
https://cdn.dribbble.com/userupload/46839565/file/still-b116e724681c5964c5d0382a2e094762.png?resize=1600x
https://cdn.dribbble.com/userupload/46940424/file/still-8e1c218e1c01dcbc265fb3cc3487d4cc.png?resize=1600x
https://cdn.dribbble.com/userupload/46914197/file/b3f3e920c24557e90447bc29de4278c1.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46934517/file/still-082fadf69163dcb6e2fd8e560afcccf7.png?resize=1600x
https://cdn.dribbble.com/userupload/46953593/file/8aa5f513144c6f82138c4e20eff45742.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46952006/file/still-022036f66659e869dbd21121bf5078d4.png?resize=1600x
https://cdn.dribbble.com/userupload/46940602/file/aeae2a5c2474c998d1890293fcb320ab.png?resize=1600x
https://cdn.dribbble.com/userupload/46940449/file/a1b67dd81be901ef394f0a7d6ba8a166.png?resize=1600x
https://cdn.dribbble.com/userupload/46952289/file/a646a8b523c592644a53584c95b6d8d1.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46953729/file/6c0b67c42237ca6c69e384ec598d5ae1.jpg?resize=1600x
https://cdn.dribbble.com/userupload/45734781/file/72b6e084ec678543f1ed58549bad90ef.png?resize=1600x
https://cdn.dribbble.com/userupload/46939872/file/d53b9f281e4592a07169455e54f05961.png?resize=1600x
https://cdn.dribbble.com/userupload/46931979/file/32d4a84f803c28fcea26c5dff194d219.png?resize=1600x
https://cdn.dribbble.com/userupload/46944516/file/2697e41b20abc9b82c639e7561f44925.png?resize=1600x
https://cdn.dribbble.com/userupload/46942791/file/b7f9206074b5cb94c31abb2228bc9e93.png?resize=1600x
https://cdn.dribbble.com/userupload/46946200/file/6a160c0b649fa6d432dd202e4b4de776.png?resize=1600x
https://cdn.dribbble.com/userupload/46938263/file/still-e1af371f80fb0d0f60ca62128b3f8510.png?resize=1600x
https://cdn.dribbble.com/userupload/46934636/file/774deb2f9ae4d8e54e54ff9ee236e001.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46934171/file/796c7172aa9bc95d3ae58dd1ae498d8d.png?resize=1600x
https://cdn.dribbble.com/userupload/46942758/file/a7e3ad6544aa296bf3cac97ad3d0cd4e.png?resize=1600x
https://cdn.dribbble.com/userupload/46942508/file/255fb22e6a7e9eba4ac0ee72bf07596c.png?resize=1600x
https://cdn.dribbble.com/userupload/46937297/file/38da431ca6c04d2188e2d27f363eb270.png?resize=1600x
https://cdn.dribbble.com/userupload/46939114/file/5773f4b22800e46bcd39540e9835b02a.png?resize=1600x
https://cdn.dribbble.com/userupload/46938007/file/df3d5f39c28c26683b1d2d6a45bce986.png?resize=1600x
https://cdn.dribbble.com/userupload/46938571/file/still-30515006b185e72cd77eed2256624bee.png?resize=1600x
https://cdn.dribbble.com/userupload/46511882/file/c99e58d2ab6ce7fcc7f323dc6fbb5e09.webp?resize=1600x
https://cdn.dribbble.com/userupload/46946024/file/97a2ed221998fa250803baac58306700.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46939948/file/67d4e739c7b90f75eaff86951e2c753d.png?resize=1600x
https://cdn.dribbble.com/userupload/46947742/file/925f9cea96c9ff9f84ab09ce2068514e.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46938093/file/ff7033c3a85180b66e1ee634327de7fe.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46945751/file/6da6d8fb72e7811fa3886bac7fb1efc4.png?resize=1600x
https://cdn.dribbble.com/userupload/46943042/file/still-2bb0d2b86f384b3600aaa61cd7201904.png?resize=1600x
https://cdn.dribbble.com/userupload/46940778/file/0378f9ef19fd930407c5193a5e8e59ee.png?resize=1600x
https://cdn.dribbble.com/userupload/46940117/file/df703a72dc1b0892e1145be9e0494dc0.png?resize=1600x
https://cdn.dribbble.com/userupload/46953919/file/707a275ff8da762786c13e43864dbefe.png?resize=1600x
https://cdn.dribbble.com/userupload/46957088/file/still-8d9441d54f4e41a9c094c289d08c5ddb.png?resize=1600x
https://cdn.dribbble.com/userupload/46940297/file/fcbc1655f5095722f7f44d0418411bc9.png?resize=1600x
https://cdn.dribbble.com/userupload/46951097/file/9098c0fc70e283b00baff0f11bd84bcb.png?resize=1600x
https://cdn.dribbble.com/userupload/46941823/file/386faedc81a2d95f7c3dfe0348ee6ba4.png?resize=1600x
https://cdn.dribbble.com/userupload/46942529/file/bbd5d3c9df3a6e596c437f399f9ea304.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46933902/file/8d57c799e19369aba504b0614daa3ba9.png?resize=1600x
https://cdn.dribbble.com/userupload/46943038/file/c0c8edb1b8f4d23714268257703e317c.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46954594/file/b72fd2239378892ca5dfcd5f89cb09a0.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46923821/file/82c57aac04a1d533ffecf1e20c76623a.png?resize=1600x
https://cdn.dribbble.com/userupload/46942194/file/5ee4a4b72e16c0cf3330e69e80718aa7.png?resize=1600x
https://cdn.dribbble.com/userupload/46930588/file/cd6e78eda4ae5432b1fd8d467fa0855b.png?resize=1600x
https://cdn.dribbble.com/userupload/46915718/file/4767f83c6099eea32ec7a5cf19af578b.png?resize=1600x
https://cdn.dribbble.com/userupload/46943085/file/b338e39f7a44575f66cc647392d0f2ad.png?resize=1600x
https://cdn.dribbble.com/userupload/46939206/file/9aa3cbd290b9ce53414b27984f862130.png?resize=1600x
https://cdn.dribbble.com/userupload/46939232/file/still-b6bcd41b1b60dc1a850ffc26bc7a411d.png?resize=1600x
https://cdn.dribbble.com/userupload/46930988/file/01ed51eac6acfe863df6e1e8a739aa1c.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46942866/file/554d475caffccbe245f14244a00b7e89.png?resize=1600x
https://cdn.dribbble.com/userupload/46955165/file/still-8d633184101e9818b8c804ac539dbbd9.png?resize=1600x
https://cdn.dribbble.com/userupload/46952518/file/still-701ff1953667d3d53adbf1f973e76267.png?resize=1600x
https://cdn.dribbble.com/userupload/46955814/file/71b9bee6f0a1e10f0debef7df5bbb8fa.png?resize=1600x
https://cdn.dribbble.com/userupload/46942367/file/still-61136f5677ad67428cc2ed891da30df3.png?resize=1600x
https://cdn.dribbble.com/userupload/46939550/file/4d358723eccc20d1d420f1d5c5a11aa4.png?resize=1600x
https://cdn.dribbble.com/userupload/46935469/file/1cddb26870b74d007f0c6bc057cdb390.png?resize=1600x
https://cdn.dribbble.com/userupload/46933819/file/ca24f60ce65015b9a32b06b8f1d2d953.png?resize=1600x
https://cdn.dribbble.com/userupload/46956590/file/811c58657efca245999b7933babd74f8.png?resize=1600x
https://cdn.dribbble.com/userupload/46947519/file/40f68231fe8a9d1ea4943d8b966044ed.png?resize=1600x
https://cdn.dribbble.com/userupload/46947221/file/5c98ecaa880e55b8a1282bf1a0f00e65.png?resize=1600x
"""

def main():
    urls = [u.strip() for u in RAW_URLS.strip().split('\n') if u.strip().startswith('http')]
    
    # Deduplicate by file hash
    seen = {}
    for url in urls:
        match = re.search(r'/file/([a-f0-9-]+)', url)
        if match:
            fid = match.group(1)
            if fid not in seen:
                seen[fid] = url
    
    unique = list(seen.values())
    print(f"Downloading {len(unique)} unique Dribbble screenshots...", flush=True)
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    success = 0
    skipped = 0
    
    with httpx.Client(follow_redirects=True, timeout=30, headers=headers) as client:
        for i, url in enumerate(unique):
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            ext = "webp" if "webp" in url or "format=webp" in url else ("jpg" if ".jpg" in url else "png")
            filename = f"dribbble-{url_hash}.{ext}"
            filepath = SCREENSHOT_DIR / filename
            
            if filepath.exists() and filepath.stat().st_size > 10000:
                skipped += 1
                continue
            
            try:
                resp = client.get(url)
                if resp.status_code == 200 and len(resp.content) > 10000:
                    filepath.write_bytes(resp.content)
                    success += 1
                    if success % 10 == 0:
                        print(f"  Downloaded {success}...", flush=True)
            except:
                pass
            time.sleep(0.2)
    
    total = len(list(SCREENSHOT_DIR.glob('*')))
    print(f"Done! Success: {success}, Skipped: {skipped}, Total: {total}", flush=True)

if __name__ == "__main__":
    main()
