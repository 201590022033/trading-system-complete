# Windows portability validation - 2026-09-06

This maintenance task does not activate OI3 or HR12. Historical reports and
research results remain unchanged.

Git 2.55.0.windows.5 has system core.autocrlf=true. No repository attributes
existed and git check-attr reported no attributes for abspj.csv. Git reported
index LF / working-tree CRLF while the tree was clean. No checkout filter was
assigned (configured LFS drivers were inactive for these paths).

abspj.csv: committed 375,816 bytes with zero CRLF; Windows checkout 378,502 bytes
with 2,686 CRLF. LF-normalizing the checkout exactly reproduces the committed
bytes and SHA256 b150c75dac36936b5dac176359eb1f8b347843d993fefc8e48489fe6737a727d.

Audited all 39 immutable baseline paths plus all remaining tracked analysis data
and results: 45 paths, 43 CRLF-only differences, no other transformations.
All baseline committed hashes matched their recorded values before restoration.
Restored the 43 affected paths directly from binary git show output, without text
decoding or regeneration. All 45 now equal their committed bytes exactly.

.gitattributes disables text conversion, filters and ident substitution and
leaves working-tree encoding unspecified for analysis/data, analysis/results,
and the six hash-pinned source files. Ordinary source/docs retain normal Git
text behavior. Existing clones need an explicit restoration from committed bytes
after auditing local changes; changing attributes alone does not refresh files.

The diagnostic's three repository text reads now specify UTF-8. Inspection of
scripts/setup_dev.py and scripts/run_tests.py found no equivalent file-read bug.
Two added regression tests emulate cp1252 and exercise actual checkout under
core.autocrlf=true/core.eol=crlf and core.autocrlf=false/core.eol=lf for all 45
paths, with a temporary index and object store. Existing immutable tests are
unchanged.

Validation: Windows Python 3.12.10 diagnostic PASS; focused development/HR11
regression tests 13 passed. Full safe suite: 184 passed, 0 failed.

## Complete byte audit

Every after hash equals the committed hash below. Affected means checkout-only
CRLF bytes were restored; no committed research content was edited.

| Path | Affected | Windows before SHA256 | Committed / after SHA256 |
| --- | --- | --- | --- |
| adaptive_technical_ensemble.py | yes | 6ad3205bc4fce9506d46124c1a1810ec0a0f74054e80a7d9555cc6c0f439c4af | 74093d1e6660734a55c79992611dc0dace83a8f4493aed97b6dcec2996e60d95 |
| analysis/data/hr2/abspj.csv | yes | e0749533033d4449671fd570bb944d267a73f99efdbd17d1f4df8af82b31f121 | b150c75dac36936b5dac176359eb1f8b347843d993fefc8e48489fe6737a727d |
| analysis/data/hr2/bhp.csv | yes | 2bd5e907d2a084ba49a44d4699ee947b8556c73c3f3d03e2cadd06e1d1518fca | d54a076020832e380bfcd9646ce8abf4494018640fba3ca46a4ea1b7da2eff49 |
| analysis/data/hr2/brent.csv | yes | a4ec8df1057a28722c31460b77e1c4d25c12d8e2fedaa969ec63b2defdfd92ce | bf2069a6a5d079734095828583f46e0da5c2d544d3c7205b5cad540b2c4dd476 |
| analysis/data/hr2/dxy.csv | yes | 60e4c3d2c840cab6e85cc36ac26cec1e34b56c1cf837130e3e7be2b86a58f2a7 | 652ec0cb6c5206ec4f285f73edf1378ebe6ed7548e0993f6a08e8e7a7b12667b |
| analysis/data/hr2/gold.csv | yes | bbfbed3edec97408ccc497ec06c53ee2cbed2ae322b80a004d626bd2de84f7ec | a24e30c458741ce738fc7d50c8476edffd980cb9afa3cda1ee6ec50c49f54629 |
| analysis/data/hr2/impj.csv | yes | 47fe9bde802b8a8c1987adf4028708f1cf02daedf85545674ea2a86d97a3648f | fd24ddf9914392eecf267c51584d9812e152de25ed3199b4a43646d9c5b991d1 |
| analysis/data/hr2/jse_all_share_proxy.csv | yes | cd932f4d72fba6daf8efb871603a6693173c11291b8d1bc2cfa36415ed372681 | 15830a06ccc17bcdf85fa0b5166e40e8db4cb01e358779e9afa78d7626e927b8 |
| analysis/data/hr2/npn.csv | yes | a546a6fdbd36117a23199bd479436a70a7f0420ef0e37cc8b92e71b24ae1d50f | 4504dcf3bbfc5393966eb52d2fc7baba47ff0c85f0db309f6d287171d389331b |
| analysis/data/hr2/palladium.csv | yes | c7b98478339b0451357961e58939208cf84bbbe988b573808821245cb9ba45a6 | 08c801b89080d9bb172fcb6be158af9542b3efb4dfaaeafcfe79a09fb49287ed |
| analysis/data/hr2/platinum.csv | yes | ae12b0e3e81735b0775b5c80abe12e95bfa62767a267116bbce02e2e67c4575d | b79ce00faadc4266892cfcc4a44844663347edaf86a3ec19a213e2e0bb49fac1 |
| analysis/data/hr2/sasol.csv | yes | 123b1ed28ea2a214afc0922ceccb30e72f6f8927f29ed31fc6e813cad09f8cf0 | c6ffd326ad5a4945438911902ac903e7983bafc4c40dfbe3f8c8fd1040328d73 |
| analysis/data/hr2/shpj.csv | yes | 8dc6fcd9ed0c625b9244726b7ecc77ac0bf8c86a8ecd88897ea2cbf1387234b6 | 80841c0fd50122128eb560d3479fddf50f45c9b172a9c2347158fed431919a4b |
| analysis/data/hr2/sp500.csv | yes | d66c5d073dd6d6c3524f6bf9dbe15218a6baada319f360277f40afc32e22a4b6 | 0251c4401794e3a97401d741cba6e2af44545f9bd495310cc1305dad00801b10 |
| analysis/data/hr2/us10y.csv | yes | 3106980d198d469a73aead3a16f956dd5e5e8b3a2c886f890e165e9962c03f5b | 28a0c52de213d4d6c6e111ac2d9aceaee63ac9389b678c79038e6f80f847ba4a |
| analysis/data/hr2/usdzar.csv | yes | 75e61bbc4a7a5269762ae756beda50b94d9c29487082f56596838ea779b5d4ce | 7cc97a5437b46102368a518b1ac141e9589925e4e66ae1b236f0b53de7493d40 |
| analysis/data/hr2/vix.csv | yes | 47eaa119cd80c316eb5778d3f775aef616a84e57e66a0a9cec1a1e65b6820eb4 | ad43aab7d5c5087500189049edb8cf187b0e9a7cb20836fcafb8b9dc79545263 |
| analysis/data/hr3/cross_asset_features.csv | yes | f80b2f462369339ad488537d9381534132fa148cdcebe443eb872470b3239e1d | 4fad72b2fcc0e40434f76b0374711915f7050ed0d1c85cabcc44bd7db167e2f4 |
| analysis/data/hr7/asset_technical_features.csv | yes | 5e244d29f3f4406c401437067cb49ebe385fe679c69bbbaf21b39b4a83dd9b52 | 42ae6a5741235327886441822f7e657ea79598a6f4d51b16c7cbc6828144f844 |
| analysis/data/hr9/adaptive_technical_decisions.csv | yes | 00c8611deec720492f4bc6f89d7b8609a58f26844346fc2f4707c9df1bdc41be | 82a4e535ea1d12b122bd2c8657b7d32735c84803e4a019c375c14a7b3eec5121 |
| analysis/data/hr9/adaptive_technical_decisions_v2.csv | yes | fd4a9c3b4cfc01239802c207dfd476608f1d64e2e9ca440a8e59069dcb832a11 | a7544ede96a1157c450e97fe69d446a20231d37a1946f91428753386ceb3cfb7 |
| analysis/results/adaptive_technical_ensemble_summary.json | yes | 63f90ec7d4fe6d554fed502f62e68d5114885db2dd5c3934b99c4c1d594ea4df | 681f0a8295e9287a292d407551666b49648767e5d602a1f49b5877b5af8a0c21 |
| analysis/results/adaptive_technical_ensemble_v2_summary.json | yes | 6d92648c5fd0410476d2134de5f8eb14366945c6196cb273d7c0adee2805e0fb | 8c5407f000f732589714660742e7aaf0c3b277febfc0f06dbad73abcc6f50abb |
| analysis/results/asset_technical_availability.json | yes | b3965fafa28e176a96fbc8f14ac1be98300811165ddf4700f720d989249b5f31 | da5476c660a21c209b72cc33ab1dd16519c0b78c54f148bcc7b733c53f0db0bf |
| analysis/results/cross_asset_feature_manifest.json | yes | 9341433cce4988085e1de94e7fd58eabc3913f4df343a77ea9c00163f8524ef8 | 0cd161f1f6ac288b3eecece1db3b05ccd7abd8222af11bc5b39e23346a5dbdc9 |
| analysis/results/forensic_analysis.json | yes | d4807c91fb6caab0712b45f0d3d7d703249db215d13bfb6e6e71bca5b6eaa7df | 5e440aa1b71fd2396004121b942a1774e0dd160e1bca443c9fe674ca81bfaae1 |
| analysis/results/forensic_price_snapshot.json | yes | 1add4146a1469d113a109d1b9bcbfac2bb7ff08e45aca4e6341317117fe359bd | 1f9f26f3d03e1f4fcd18b5d23fdbfde0c926047e8d2509f709026421ac77370a |
| analysis/results/forensic_summary.json | yes | 9013a16f6fab3322913ba1194a738ae7449a6fa229ff542cc75f3f123cff3ea5 | 759fdd56e95322d37428a6e3df40751a4569efecbfaa1b8a916cb6adc28f8220 |
| analysis/results/historical_feature_availability.json | yes | f5030a66b440751198e41817f28b0d0d478920f37ede9da86debd009f960ab28 | 0ed3c97f9084cd828f27566eacb536c4ed16a06a62ef8a32ce1c4988096a652c |
| analysis/results/historical_feature_store_schema.json | yes | abbd42796abd4ac2617706af194840ad3fb87fb9302546f5ebd62f44071ea74c | e5ba3b6a9b7b04db7c46c3fa6fd508aa4c39671452566d428b779e53c9cd3312 |
| analysis/results/hr10_robustness.json | yes | 04c30d6f18d3357b214890f9aee94841cb9e2d6450bed7749e58bf0811e8cc95 | 01679ea7b0142ec1fe8407929fa1fb71bd829c43ec30d9c9d1085913c1299733 |
| analysis/results/hr11/baseline.json | yes | b42d914a13c5300c1cf4eec3ff516242b05a51fd89e07395a50a94e9946b93ec | 0c0bd5ec4d2c804a4a665ba9a1487096b035df8fcec44612bbefcf492def6fdf |
| analysis/results/hr11/decisions.jsonl | no | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| analysis/results/hr11/report.json | yes | 90fbc62bf93ab0cdd7dec5f4f0ecc710d753ad335596bd592e9f4e97979b2d3b | 048fda40e27a8801b5504910a2c4d90be958d81e6346490348d98ea00ca7c6a0 |
| analysis/results/hr11/report.md | yes | 312a0e64bf12829fb7d66f65c392f9bbc9960dab2e09f923911663e623028200 | cdbd29022048e35f6a2755ea2c06de9bf576b9610d82811bb0a0a6be0c6863f1 |
| analysis/results/hr11/trades.jsonl | no | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 | e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 |
| analysis/results/hr11/validation.json | yes | 434c47e1c9b128f84a1cdcc1edc18d631600e66be06b563da1aae1d9f7e86747 | a53582da09e0a3ff7ceebc161e12b5769a65f90b067b8242c266a3952ca4a983 |
| analysis/results/hr9_adaptive_ensemble_evaluation.json | yes | 81626f729928d4c56e843e7352ccf131787ba97449b64060ec4511b12edad9e6 | b5465378fe15c643b9719991c5df7a27dc4679932a2c8967fcd8448b1b0e46c6 |
| analysis/results/indicator_effectiveness.json | yes | 4b9ea69488c9c9d3bf165d8ae6a72873e72ae83f1a294090fe4efc5bee054eac | 77fd1cf7dbb52857e68bec15e65ac81739725163fee1bde6d49a8c89775b13f7 |
| analysis/results/technical_feature_registry.json | yes | 9558b96ca969cde69fb3618b4f4776b039ead0e130906e98923d8705259a8dd9 | 3d8d399227ac29fc7bfac9b2472a4194d4f213704f61fd995cd2e6c1d275f878 |
| cross_asset_features.py | yes | b0ba714c41409b9810977dc767f1ffaa1227aa49f39045bb09d34a668a091420 | 04352fad390ee56e18e0bf0af52f6eca4ca1bc40d901f2e07e7a4c4c4f0efb68 |
| hr10_robustness.py | yes | cf1aaf137fe6b74b270d43125a53398f6df0c20762469fd3c8a9c53226a3b23d | af0b78b7dbc91ecc9a9fd00ea2fd0588fd76ed100ef384c47d61cbb4d496eb20 |
| indicator_effectiveness.py | yes | cbde1d9e0a79a56981d7fb99058e4ca683792f217eb58d37277111b72d434435 | 57ccaa1390dc33218e14db1d48f5d9e9fa784b8ff5b1b2ef688004913f1d645b |
| market_profiles.py | yes | 1e9bfdf34b6bd4bb3dd9e9373e31cc8c99c9397828be6ad8979bb726192b9210 | d12915cf08ee1de943f15511ac77a36c2d3be0a1865860e89604c215e2a1ec29 |
| technical_signals.py | yes | 9889c7c143990ac45c4b6b9a571c30850f64be067e115c9e204dec95b05c5742 | eceed1af2e1e833e10693e64990e75e80ec46c0ffd93cb4fa1ec1180e8f69d98 |
