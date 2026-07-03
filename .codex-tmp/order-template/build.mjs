import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const outputDir = "/Users/puff/Desktop/Puff/Puff-system/outputs/order-import-template";
const desktopPath = "/Users/puff/Desktop/订单管理导入模板.xlsx";
await fs.mkdir(outputDir, { recursive: true });

const workbook = Workbook.create();
const sheet = workbook.worksheets.add("订单导入模板");
const guide = workbook.worksheets.add("填写说明");

sheet.showGridLines = false;
sheet.getRange("A1:G1").values = [["日期", "作业要求", "模板", "格式", "学校", "价格", "支付方式"]];
sheet.getRange("A1:G1").format = {
  fill: "#123B32",
  font: { bold: true, color: "#FFFFFF", size: 11 },
  horizontalAlignment: "center",
  verticalAlignment: "center",
  borders: { preset: "outside", style: "thin", color: "#123B32" },
};
sheet.getRange("A1:G1").format.rowHeight = 28;
sheet.freezePanes.freezeRows(1);

const widths = [14, 42, 24, 14, 24, 14, 16];
for (let index = 0; index < widths.length; index += 1) {
  sheet.getRangeByIndexes(0, index, 21, 1).format.columnWidth = widths[index];
}

sheet.getRange("A2:G21").format = {
  font: { color: "#243B35", size: 10 },
  verticalAlignment: "center",
  borders: {
    insideHorizontal: { style: "thin", color: "#E4EBE7" },
    bottom: { style: "thin", color: "#D6E0DB" },
  },
};
sheet.getRange("A2:G21").format.rowHeight = 24;
sheet.getRange("A2:A1001").format.numberFormat = "yyyy-mm-dd";
sheet.getRange("F2:F1001").format.numberFormat = "0.00";
sheet.getRange("B2:B1001").format.wrapText = true;

sheet.getRange("D2:D1001").dataValidation = {
  rule: { type: "list", values: ["Figma", "Psd", "Xd", "Jsd", "Html", "定做", "无"] },
};
sheet.getRange("G2:G1001").dataValidation = {
  rule: { type: "list", values: ["微信", "咸鱼", "小红书", "支付宝"] },
};

guide.showGridLines = false;
guide.getRange("A1:D1").merge();
guide.getRange("A1:D1").values = [["订单导入模板 · 填写说明"]];
guide.getRange("A1:D1").format = {
  fill: "#123B32",
  font: { bold: true, color: "#FFFFFF", size: 16 },
  verticalAlignment: "center",
};
guide.getRange("A1:D1").format.rowHeight = 36;
guide.getRange("A3:B10").values = [
  ["字段", "填写要求"],
  ["日期", "必填，使用 YYYY-MM-DD，例如 2026-07-03"],
  ["作业要求", "必填，1～500 个字符"],
  ["模板", "必填，1～100 个字符"],
  ["格式", "必填，请使用单元格下拉选项"],
  ["学校", "必填，1～100 个字符"],
  ["价格", "必填，最低 0.01，最多两位小数"],
  ["支付方式", "必填，请使用单元格下拉选项"],
];
guide.getRange("A3:B3").format = {
  fill: "#DDEDE6",
  font: { bold: true, color: "#123B32" },
};
guide.getRange("A3:B10").format.borders = { preset: "all", style: "thin", color: "#D6E0DB" };
guide.getRange("A3:A10").format.columnWidth = 16;
guide.getRange("B3:B10").format.columnWidth = 58;
guide.getRange("A12:D12").merge();
guide.getRange("A12:D12").values = [["注意：不要修改“订单导入模板”工作表第一行的表头；单个文件最多导入 1000 条订单。"]];
guide.getRange("A12:D12").format = {
  fill: "#FFF4D6",
  font: { color: "#7A5617" },
  wrapText: true,
};
guide.getRange("A12:D12").format.rowHeight = 32;

const preview = await workbook.render({
  sheetName: "订单导入模板",
  range: "A1:G12",
  scale: 1.5,
  format: "png",
});
await fs.writeFile(`${outputDir}/preview.png`, new Uint8Array(await preview.arrayBuffer()));

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(`${outputDir}/订单管理导入模板.xlsx`);
await output.save(desktopPath);

const check = await workbook.inspect({
  kind: "table",
  range: "订单导入模板!A1:G5",
  include: "values,formulas",
  tableMaxRows: 5,
  tableMaxCols: 7,
});
console.log(check.ndjson);
const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 50 },
  summary: "final formula error scan",
});
console.log(errors.ndjson);
