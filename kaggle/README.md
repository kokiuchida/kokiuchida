## Kaggleの開発環境構築手順（uvで環境構築）
1. github上にプロジェクトを作成する（Kaggle配下）
2. WSLから```code .```でVSCodeを開く
3. このリポジトリをクローンし、1.で作成したプロジェクトに移動する
4. git init でUV環境を構築する

## 注意事項
- 必ず各コンペ用のプロジェクト毎独立してUV環境を構築する
  - kaggleリポジトリと同階層でuv init をして上位フォルダにtomlファイルが作成されてしまうと、配下のUVと競合してエラーが頻発する

## other
- KaggleのデータをstreamlitでWebアプリ化
