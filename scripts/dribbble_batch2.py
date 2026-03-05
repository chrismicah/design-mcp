"""Download batch 2 of Dribbble screenshots from browser-collected CDN URLs."""
import httpx
import hashlib
import time
import re
from pathlib import Path

SCREENSHOT_DIR = Path(__file__).parent.parent / "screenshots" / "dribbble"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

RAW_URLS = """
https://cdn.dribbble.com/userupload/46932671/file/fbf52ac5c5e35251675367deab2a8b50.png?resize=1600x
https://cdn.dribbble.com/userupload/46932758/file/edc597e1a4038dc6d4dc858b9a5062ce.png?resize=1600x
https://cdn.dribbble.com/userupload/46944809/file/still-dd2fdd3d92d8209504c4eff59e0b3588.png?resize=1600x
https://cdn.dribbble.com/userupload/46947151/file/78a81659dfb8648a0d69fc08b3f9dfb3.png?resize=1600x
https://cdn.dribbble.com/userupload/46936512/file/e188b17b5ee312efd638d20ec5dd7302.png?resize=1600x
https://cdn.dribbble.com/userupload/46958621/file/05ff8e5242d859702b8e91bcafba289b.png?resize=1600x
https://cdn.dribbble.com/userupload/46934170/file/still-aebed27da22ba1d36650ea8a2d624d8b.png?resize=1600x
https://cdn.dribbble.com/userupload/46939560/file/6cc5454c5ea14cadcdba21ae73f18241.png?resize=1600x
https://cdn.dribbble.com/userupload/46939475/file/d1b4c98abbb10bf401ceaeaafd499f70.png?resize=1600x
https://cdn.dribbble.com/userupload/46941100/file/434734864f72d0abe159d4abbc428b98.png?resize=1600x
https://cdn.dribbble.com/userupload/46959441/file/21ae1a9a293af57249d03dc6a8cfc171.png?resize=1600x
https://cdn.dribbble.com/userupload/46934335/file/c874f096fb810dc3034c7e38c31afc68.png?resize=1600x
https://cdn.dribbble.com/userupload/46945697/file/still-39a75305b9cd1ab0de043c6663e04733.png?resize=1600x
https://cdn.dribbble.com/userupload/46918329/file/e9ade55309ffb9fa454f9c9e10f6bed0.png?resize=1600x
https://cdn.dribbble.com/userupload/46930405/file/0740a8cdf7159ac4601e14d3deb5f0a3.png?resize=1600x
https://cdn.dribbble.com/userupload/46938399/file/d009e79aca0b0f52fa04925507a950e7.png?resize=1600x
https://cdn.dribbble.com/userupload/46932879/file/1ea84ae74c0ef2f51caee3c3f4f4c4c9.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46938992/file/b780468d95462a6f5efcab7479fa5c55.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46939223/file/63f54f37198f4333e6c1061049297b8b.png?resize=1600x
https://cdn.dribbble.com/userupload/46931939/file/0f9b5417cbcd46a1d2d196ea3690158b.png?resize=1600x
https://cdn.dribbble.com/userupload/46957976/file/still-3498cd32fb0113cdb31658a67202ec98.png?resize=1600x
https://cdn.dribbble.com/userupload/46929898/file/still-89cab2c775e89c6b7b5822cbd3ffabf9.png?resize=1600x
https://cdn.dribbble.com/userupload/46944114/file/3f7c8392647665f9a7b2ffca7ca7973c.png?resize=1600x
https://cdn.dribbble.com/userupload/46939898/file/04aca76d6a7391b8d2d0e1ccf911aab7.png?resize=1600x
https://cdn.dribbble.com/userupload/46936134/file/bca1361260c6a77a04980d2945fe1dd9.png?resize=1600x
https://cdn.dribbble.com/userupload/46932537/file/007d488738828168c87e54b94e623aa8.png?resize=1600x
https://cdn.dribbble.com/userupload/46948400/file/ef47e6323bcb2be7dae2b4b3cf3812d2.png?resize=1600x
https://cdn.dribbble.com/userupload/46947332/file/1d23ebd0ebc1b141a93df8a4907e9ab7.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46940154/file/006bd17557e383a2e6511cb6747dca77.png?resize=1600x
https://cdn.dribbble.com/userupload/46943171/file/still-4f8e44184c03e28614bce7e8718cebb4.png?resize=1600x
https://cdn.dribbble.com/userupload/46942456/file/e1c9349b2efb824adbb20dfd601ed4da.png?resize=1600x
https://cdn.dribbble.com/userupload/46939952/file/still-030f5b4df089aa903363ae462c277434.png?resize=1600x
https://cdn.dribbble.com/userupload/46931166/file/df62fa1518a24f6b9c51b7a45f9292db.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46939842/file/c7c3f85e13aafeb95ebd64e6247d10ac.png?resize=1600x
https://cdn.dribbble.com/userupload/46956456/file/df36e4065bf896857c8cdfccb0302a09.png?resize=1600x
https://cdn.dribbble.com/userupload/45900062/file/still-18b39db2477e034d7bf4536b41c8f760.png?resize=1600x
https://cdn.dribbble.com/userupload/46933680/file/15d96cc626c1dcaeb3bc2de0884a0197.png?resize=1600x
https://cdn.dribbble.com/userupload/46914165/file/bf8f131400f9493ee5baea6e850d710b.png?resize=1600x
https://cdn.dribbble.com/userupload/46929003/file/still-648a634bc702fc9de5e2d411ca2fb122.png?resize=1600x
https://cdn.dribbble.com/userupload/46929920/file/ed49b8d39c70402389691d9ee60c8b3c.png?resize=1600x
https://cdn.dribbble.com/userupload/46929379/file/abacb7e54422e58a55df4dc23400d1bd.png?resize=1600x
https://cdn.dribbble.com/userupload/46933164/file/still-cd5afb2f597ede93fd8c27a839a1b72c.png?resize=1600x
https://cdn.dribbble.com/userupload/46917768/file/e9e890c04150617456f7f3caee2d2178.png?resize=1600x
https://cdn.dribbble.com/userupload/46928964/file/12a130dc3dd6c70e776bae8088a5701f.png?resize=1600x
https://cdn.dribbble.com/userupload/46931286/file/5da0462f2045bcf41df1e7d3cc6af286.png?resize=1600x
https://cdn.dribbble.com/userupload/46945917/file/f367178fd8c631bce2c8ce358d31b92c.png?resize=1600x
https://cdn.dribbble.com/userupload/46927643/file/ef5e0412b97b58d87e9cf64f86f9adaa.png?resize=1600x
https://cdn.dribbble.com/userupload/46922885/file/c031e32e405432d760b63fc729981036.png?resize=1600x
https://cdn.dribbble.com/userupload/46938916/file/1f9dbcc685f07ce875c7d998623b0a68.png?resize=1600x
https://cdn.dribbble.com/userupload/46928631/file/1ea23ff12e1ac6bbbeaacf06e349b49d.png?resize=1600x
https://cdn.dribbble.com/userupload/46938786/file/f3feb7db0dec482b1d566ac8c6c78e96.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46939283/file/f30fc2f064e0e3dcf12f360b1fe5dde2.png?resize=1600x
https://cdn.dribbble.com/userupload/46930902/file/200951dd32c15444c48d08678bd71a43.png?resize=1600x
https://cdn.dribbble.com/userupload/46930081/file/f2b3646414f2d58e495da5b9572107c1.png?resize=1600x
https://cdn.dribbble.com/userupload/46917263/file/still-bdcb699e4451c9ee146bdf5ab39338b8.png?resize=1600x
https://cdn.dribbble.com/userupload/46929832/file/a56153291eae1f639b9f3fae645f0e29.png?resize=1600x
https://cdn.dribbble.com/userupload/46949323/file/180d08907e6332b807a1e18999deab3f.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46929138/file/a4338a7897570af8a9d98e5956007cff.png?resize=1600x
https://cdn.dribbble.com/userupload/46947891/file/7e684cf0c80241c42fabecdd41cc5c96.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46926535/file/74ad29adbf4bd8a9337ab1a016cbb518.png?resize=1600x
https://cdn.dribbble.com/userupload/46940608/file/8affee486d0d0efcc6a7775fc8602b59.jpeg?resize=1600x
https://cdn.dribbble.com/userupload/46926277/file/28514e4152011dc3512401f191ee5f87.png?resize=1600x
https://cdn.dribbble.com/userupload/46926141/file/bc48b34f36ebb209d7b8f272e288505f.png?resize=1600x
https://cdn.dribbble.com/userupload/46829920/file/still-c8012019cb4152d50332fd14f7198507.png?resize=1600x
https://cdn.dribbble.com/userupload/46938828/file/3b1457f1fe64ef035bf53379aed4cccc.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46948572/file/c110fb8c68a27d57bc11048e722a3a4e.png?resize=1600x
https://cdn.dribbble.com/userupload/46927487/file/3d86b275dedbc14c6642f7cfc052aeea.png?resize=1600x
https://cdn.dribbble.com/userupload/46936357/file/c951c331831005abe53dbde13045f6c7.png?resize=1600x
https://cdn.dribbble.com/userupload/46924986/file/429643469337b636f06819f9d41ed32a.png?resize=1600x
https://cdn.dribbble.com/userupload/46944452/file/04ef979f279f1b4183b7a771e9f6dcb4.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46925584/file/146a4a0dc48b21f5690da50ab6dabaa8.png?resize=1600x
https://cdn.dribbble.com/userupload/46928037/file/95ce35fbd71259a087afe831a768026f.png?resize=1600x
https://cdn.dribbble.com/userupload/46930265/file/1ecf9197baca344c2fda9a2a233e471b.png?resize=1600x
https://cdn.dribbble.com/userupload/46926367/file/2690e2f219260fc185287af1efe96057.png?resize=1600x
https://cdn.dribbble.com/userupload/46928623/file/8ecd8b799bd3bc5d0c001c52e1b4a560.png?resize=1600x
https://cdn.dribbble.com/userupload/46925694/file/b2d83202a34f74595a163e4b60972993.png?resize=1600x
https://cdn.dribbble.com/userupload/46921316/file/8cfb9da6dbbdc31142dc0718daa7060c.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46923880/file/1eb94a4b4814ee2ce6bf39b356a452a7.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46929266/file/ff48dd66ac6b27ba20439059ffece381.png?resize=1600x
https://cdn.dribbble.com/userupload/46946306/file/eef17145e5b3d5a8a49e0823fb9dad31.png?resize=1600x
https://cdn.dribbble.com/userupload/46924857/file/535117a1f5347c7f734dc9b27f5695f3.png?resize=1600x
https://cdn.dribbble.com/userupload/46925701/file/75c1d2d21bcb27ea7df197cca79bc6b4.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46941536/file/f95f9b2e08223099bc5f40eb60457beb.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46925545/file/862424e484cec05a8f82acd7e64de6a2.png?resize=1600x
https://cdn.dribbble.com/userupload/46854785/file/caa31947b06fe39ae596c96d23348220.png?resize=1600x
https://cdn.dribbble.com/userupload/46925684/file/f517eb82cf162b2502a56ee74862cc61.png?resize=1600x
https://cdn.dribbble.com/userupload/46944984/file/429c619c98b588c6cdd6b34e1a7b95ea.png?resize=1600x
https://cdn.dribbble.com/userupload/46925761/file/56f4e6e82e9c0d1e9857be57317d6514.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46921123/file/c265f14fe65ac52eadbdddd95671e0cc.png?resize=1600x
https://cdn.dribbble.com/userupload/46952126/file/6e0817caa52643f61a8495abf4c37d79.png?resize=1600x
https://cdn.dribbble.com/userupload/46927341/file/0a33620fd352e48127d70140cabcfb10.png?resize=1600x
https://cdn.dribbble.com/userupload/46754283/file/a64caefa0ce88ef4538a299031ae0490.png?resize=1600x
https://cdn.dribbble.com/userupload/46927041/file/26cdac6390fa0dacd3a24f0d4fbc147d.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46930043/file/5065590954c308a951ce80dace57480b.png?resize=1600x
https://cdn.dribbble.com/userupload/46942628/file/a6b922a646a8ee1488556465a2c1e2a8.png?resize=1600x
https://cdn.dribbble.com/userupload/46925900/file/41df23b9a44e65130c8160ab4f5c4347.png?resize=1600x
https://cdn.dribbble.com/userupload/46926841/file/9b8b5e12b65e9ad2fef7e1dca841718e.png?resize=1600x
https://cdn.dribbble.com/userupload/46935320/file/0f2cc4b00617a34c82b0437b494ec93e.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46929665/file/4b84e7cdfab15c0a307ba8e89be85207.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46931724/file/10cc862c013204afde1b6459d5554c68.png?resize=1600x
https://cdn.dribbble.com/userupload/46940744/file/00c78a4de15fa3c576115b1e4234e8d8.png?resize=1600x
https://cdn.dribbble.com/userupload/46908285/file/78f9b50597a4e293d123a114bff51ab0.png?resize=1600x
https://cdn.dribbble.com/userupload/46939885/file/32d322036af1b2f90b707d388a9c5fc8.png?resize=1600x
https://cdn.dribbble.com/userupload/46926851/file/39a953fa35eeae3b4ffc312b2241c738.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46924848/file/still-03047a357d15f195a325ffe3161e2d7b.png?resize=1600x
https://cdn.dribbble.com/userupload/46929278/file/33ebe2a569ce2f2af6333f8b5ed93717.png?resize=1600x
https://cdn.dribbble.com/userupload/46935633/file/fb1016cc757cee41d83a6a6f89a29038.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46920180/file/0a29e701e27825bb1b79ed6500a9edfb.png?resize=1600x
https://cdn.dribbble.com/userupload/46932094/file/still-e13bc98004b72b2ad55d08d71fd9e54f.png?resize=1600x
https://cdn.dribbble.com/userupload/46925474/file/75492946da4599a8bd7de05ec87dd8d1.png?resize=1600x
https://cdn.dribbble.com/userupload/46928634/file/ea3e7d3ad27204c4dca45b98d30be895.png?resize=1600x
https://cdn.dribbble.com/userupload/46942107/file/cec3b96466729500bbecef4671807ccb.png?resize=1600x
https://cdn.dribbble.com/userupload/46929877/file/still-355cd4381358a582f9e70aaf3478b12e.png?resize=1600x
https://cdn.dribbble.com/userupload/46923453/file/70fa6a99ea33a616ecd6c6ac9d9e6df8.png?resize=1600x
https://cdn.dribbble.com/userupload/46927241/file/66d7a400a41af00ef326e5c8aa7a1f97.png?resize=1600x
https://cdn.dribbble.com/userupload/46922997/file/3c2c044d6629e12c20bf48123ce992e3.webp?resize=1600x
https://cdn.dribbble.com/userupload/46926226/file/f3a2b14b5f307b82116421ffde8db3c2.png?resize=1600x
https://cdn.dribbble.com/userupload/46935174/file/still-e690564537f6c767f46b0560ebc04a81.png?resize=1600x
https://cdn.dribbble.com/userupload/46861905/file/f307264322bff6aca5209f07475e3cbf.png?resize=1600x
https://cdn.dribbble.com/userupload/46953159/file/d347876330793ab8ccad8d6c7991ecb8.png?resize=1600x
https://cdn.dribbble.com/userupload/46954836/file/247c33323e372129bcb6072d54092e3f.jpg?resize=1600x
https://cdn.dribbble.com/userupload/45284205/file/043871f6ea9ee173974eb102612793b4.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46954957/file/a8fb08b8d68aee0d00191d4304a9dd35.png?resize=1600x
https://cdn.dribbble.com/userupload/46945810/file/c6af7872c23cbffcda1977b941a36e26.png?resize=1600x
https://cdn.dribbble.com/userupload/46946477/file/0f2f8034909491b0b954f700d3b5791d.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46953737/file/still-6c6ea60953c97330611aa817f13511a4.png?resize=1600x
https://cdn.dribbble.com/userupload/46949940/file/7f745ec22a19523d5810d7e3b3f97737.png?resize=1600x
https://cdn.dribbble.com/userupload/46950927/file/36177e6c7ae636c3300b1ca360deae95.png?resize=1600x
https://cdn.dribbble.com/userupload/46945382/file/f02ac230e3b42ca46c79636373d548b0.png?resize=1600x
https://cdn.dribbble.com/userupload/46941675/file/cb803cb75226b3ca1c7442a12b83f061.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46956071/file/ce9dea6117c9fa9222c8433f3ec946c1.png?resize=1600x
https://cdn.dribbble.com/userupload/46956974/file/52d1c9b62fd44f89c77e6ca2c2a38468.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46949734/file/9ae26fd41bd201557359cec21c94c9be.png?resize=1600x
https://cdn.dribbble.com/userupload/46949991/file/still-a60f4ac0830ac0c082a2fdbda25753b6.png?resize=1600x
https://cdn.dribbble.com/userupload/46950384/file/c26aba1bb6a41f0ae87eca0ff79c6b7e.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46943083/file/8032a481a127a778b53c151abb36855b.png?resize=1600x
https://cdn.dribbble.com/userupload/46944975/file/01ee7a6b954341efd9c9565134a40a91.png?resize=1600x
https://cdn.dribbble.com/userupload/46945966/file/14206ec8a142366d440969bf41930b8b.png?resize=1600x
https://cdn.dribbble.com/userupload/46955904/file/d76e18949595d387c8535ff6fb7aeabb.png?resize=1600x
https://cdn.dribbble.com/userupload/46946683/file/still-3bb799c684d01efc44da91195afc2bee.png?resize=1600x
https://cdn.dribbble.com/userupload/46940988/file/84d739db17de4bc4bdbf4a3bff9b9110.png?resize=1600x
https://cdn.dribbble.com/userupload/46645352/file/1d5614f3d2d70b1e41c0cf36a849c8fd.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46958612/file/b4da3851d3fcb214845ba15a75211881.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46950302/file/326a22e9d3c9fdd8b1dd76be30313feb.png?resize=1600x
https://cdn.dribbble.com/userupload/46940656/file/still-7536dce8dacf296aa7366ac657a9b524.png?resize=1600x
https://cdn.dribbble.com/userupload/46951219/file/0d181c2dad5a8f059e2bcde5d0994df7.png?resize=1600x
https://cdn.dribbble.com/userupload/46942532/file/4892b6daf44280b71f0b5089c54620c9.png?resize=1600x
https://cdn.dribbble.com/userupload/46939745/file/30e380744bec143c7813ff9392d1ad50.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46951988/file/still-302974d6b0829c5af636b3da70d1e73c.png?resize=1600x
https://cdn.dribbble.com/userupload/46929855/file/97c597cc6ef458301cf706da5ee7cc32.png?resize=1600x
https://cdn.dribbble.com/userupload/46939298/file/37bf75c5699f4e08c99c44b4c2af028e.png?resize=1600x
https://cdn.dribbble.com/userupload/46957557/file/still-be4cb76724e2f3daa4004e1b5d004aea.png?resize=1600x
https://cdn.dribbble.com/userupload/46945589/file/still-9db04b0b35cd934afbc1d559610dca9f.png?resize=1600x
https://cdn.dribbble.com/userupload/46949977/file/8e0b6a22d987551a2dde770bbbdf7d7b.png?resize=1600x
https://cdn.dribbble.com/userupload/46938843/file/c0f8c67bd4ace498ebc21d40b60e5339.png?resize=1600x
https://cdn.dribbble.com/userupload/46676839/file/still-0d040096f3a6fab28802cb251926ff07.png?resize=1600x
https://cdn.dribbble.com/userupload/46941959/file/a054fdc8e3336b363ac1dc9d0715c9bb.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46950996/file/still-be3612b449f5c15f572aafba1bd445f1.png?resize=1600x
https://cdn.dribbble.com/userupload/46939969/file/0a412e106f0d6fb22120d9d8ec406a56.png?resize=1600x
https://cdn.dribbble.com/userupload/46939498/file/8c97a666de11a3a399389473b49fc8f7.png?resize=1600x
https://cdn.dribbble.com/userupload/46950946/file/1bd054dd4fbf9deb2258d6bba254d83a.png?resize=1600x
https://cdn.dribbble.com/userupload/46952389/file/still-86a412d1791dc9ec39909da650370a33.png?resize=1600x
https://cdn.dribbble.com/userupload/46952537/file/still-199aa2ad604cefa3bd5340cc2feabb4c.png?resize=1600x
https://cdn.dribbble.com/userupload/46828290/file/7b2023e0f131cf97a0245026160e2e1e.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46944492/file/b5f2bf3fd1abbade22b34981d3bdc6d4.png?resize=1600x
https://cdn.dribbble.com/userupload/46956193/file/5854808f91656ee782c9c2456867cf94.png?resize=1600x
https://cdn.dribbble.com/userupload/46940313/file/eca2d94e3281f387a4523815a8ef9b59.png?resize=1600x
https://cdn.dribbble.com/userupload/46938702/file/0021b5ffc79cfc752c3c972ad917ef71.png?resize=1600x
https://cdn.dribbble.com/userupload/46949993/file/36bde8544b1065cf1ff72e3eac9708be.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46944723/file/1bd4e7d7f8c3c0f97769ca5fa3e9d36d.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46915368/file/c7412621e6269da4dc3ae4ee74a72261.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46944684/file/a8bada919422afecf73bbcc7c34728f0.png?resize=1600x
https://cdn.dribbble.com/userupload/46942647/file/6597cd528e0de3c945162191650cbd33.png?resize=1600x
https://cdn.dribbble.com/userupload/46944352/file/e83ce8105f9b3048f0b898f3353cd4fa.png?resize=1600x
https://cdn.dribbble.com/userupload/46944098/file/bd2412d3d637b69c4d45b0deb0df9e0b.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46941398/file/6ea73c46a59c8d993361d7deae5ea243.png?resize=1600x
https://cdn.dribbble.com/userupload/46863289/file/60cdd77ec1bba001a20d80af5e12fe3e.webp?resize=1600x
https://cdn.dribbble.com/userupload/46941058/file/349a36d6fabf1fd32ea99093fcd212d2.png?resize=1600x
https://cdn.dribbble.com/userupload/46938617/file/758b6f3a7c13e9ca248d03e1a5b06b41.png?resize=1600x
https://cdn.dribbble.com/userupload/46915015/file/still-329f441c9ef57bd3370a5c0f032f60aa.png?resize=1600x
https://cdn.dribbble.com/userupload/46950074/file/936815d5c3af91ae63df0fc651d96cd2.png?resize=1600x
https://cdn.dribbble.com/userupload/46938280/file/5fd590a2b45c41b79ed2081b3474456a.png?resize=1600x
https://cdn.dribbble.com/userupload/46940786/file/38429e3d6a86a9df25fc07bb220fb6cd.png?resize=1600x
https://cdn.dribbble.com/userupload/46940305/file/c2b236aba7c37bd98728592db268c69d.png?resize=1600x
https://cdn.dribbble.com/userupload/46921427/file/3261c0643203ba81544a65876252c29f.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46941714/file/36e40f654e69d291c5ad7c00a3c23f2c.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46941702/file/75274bff813fca8f4a5cb99467515aa1.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46938120/file/3e3db2da22481a90d49469eb55665488.png?resize=1600x
https://cdn.dribbble.com/userupload/46939265/file/9a56c4bf443a267f97e75c3ea0579974.png?resize=1600x
https://cdn.dribbble.com/userupload/46932561/file/bfc9af2014952bcdf764425a59a07358.png?resize=1600x
https://cdn.dribbble.com/userupload/46937891/file/d2c71d0953b02f70a5d77c0fb85ab6c7.png?resize=1600x
https://cdn.dribbble.com/userupload/46950568/file/bee9f1ec971656a67cf770de3295a381.png?resize=1600x
https://cdn.dribbble.com/userupload/46938853/file/b4f07ddf9b603dff60889c205ef2e3be.png?resize=1600x
https://cdn.dribbble.com/userupload/46933133/file/still-5ebb411c2c9b3e9a08d590b0ec4099d1.png?resize=1600x
https://cdn.dribbble.com/userupload/46958381/file/649f47d6e3366a5a4973fddf0b298604.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46957739/file/bc79b5df4eebba5ca0c40c472e61a84c.png?resize=1600x
https://cdn.dribbble.com/userupload/46956978/file/649dd395e67b84c7eaa6c7fc400a43fb.png?resize=1600x
https://cdn.dribbble.com/userupload/46933023/file/still-f1a983f354d22164127a81888f7002ff.png?resize=1600x
https://cdn.dribbble.com/userupload/46955786/file/fb7bf184a30e73a50ccf3190e0216006.png?resize=1600x
https://cdn.dribbble.com/userupload/46938338/file/still-03f0eb28fdb57b6a19f1f0daeddc390d.png?resize=1600x
https://cdn.dribbble.com/userupload/46930892/file/still-f2a1f44a26766a943f0c3e191d81d4ac.png?resize=1600x
https://cdn.dribbble.com/userupload/46938162/file/a79d8410eddd7a99d104ed23eb7d69bd.png?resize=1600x
https://cdn.dribbble.com/userupload/46941487/file/85fd87349e34e1bead1319faf175be23.png?resize=1600x
https://cdn.dribbble.com/userupload/46942659/file/still-bc3dddc354c57e7791e873dc78b790e9.png?resize=1600x
https://cdn.dribbble.com/userupload/46946807/file/b5993343c08d6f657553f16e8905beb5.png?resize=1600x
https://cdn.dribbble.com/userupload/46946475/file/a4d4e2e46b7d0fab45605a86856388aa.jpg?resize=1600x
https://cdn.dribbble.com/userupload/45229255/file/a3b9295472aae9a0c94572d9bd8b7406.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46907011/file/e59df23a0b897fde7484b76a6adc679d.png?resize=1600x
https://cdn.dribbble.com/userupload/46938245/file/759b2e2b06c7b4fa3f504dd629086ff1.jpg?resize=1600x
https://cdn.dribbble.com/userupload/46945969/file/d0bf071913a5ac80ce1744fa7298e7cb.png?resize=1600x
https://cdn.dribbble.com/userupload/46892365/file/163eb15941a82bed4075c08c92855a93.png?resize=1600x
https://cdn.dribbble.com/userupload/46904319/file/e86cea3e8f9fd39815b3f1ca21e3bc64.png?resize=1600x
https://cdn.dribbble.com/userupload/46948821/file/162b9bcdc1aa28a14493f980f6e369d8.jpg?resize=1600x
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
    print(f"Downloading {len(unique)} Dribbble screenshots (batch 2)...", flush=True)
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    success = 0
    skipped = 0
    failed = 0
    
    with httpx.Client(follow_redirects=True, timeout=30, headers=headers) as client:
        for i, url in enumerate(unique):
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            if '.jpg' in url or '.jpeg' in url:
                ext = 'jpg'
            elif '.webp' in url:
                ext = 'webp'
            else:
                ext = 'png'
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
                    if success % 25 == 0:
                        print(f"  Downloaded {success}...", flush=True)
                else:
                    failed += 1
            except:
                failed += 1
            time.sleep(0.15)
    
    total = len(list(SCREENSHOT_DIR.glob('*')))
    print(f"Done! New: {success}, Skipped: {skipped}, Failed: {failed}, Total Dribbble: {total}", flush=True)

if __name__ == "__main__":
    main()
