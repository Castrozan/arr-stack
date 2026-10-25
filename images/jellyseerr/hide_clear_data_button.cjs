const fs = require("node:fs");

const identifier = "[$\\w]+";
const elementFactory = (name) =>
  `(?:\\(0,${identifier}\\.${name}\\)|${identifier}\\.${name})`;
const clearDataBlock = new RegExp(
  `${elementFactory("jsxs")}\\("div",\\{children:\\[${elementFactory("jsxs")}\\(${identifier}\\.Z,\\{onClick:\\(\\)=>${identifier}\\(\\),(?=(?:(?!"div")[^])*?\\.manageModalClearMedia\\))`,
  "g",
);

const builtPages = process.argv.slice(2);
if (builtPages.length === 0) {
  throw new Error("No built page renders the Clear Data button");
}
for (const builtPage of builtPages) {
  const source = fs.readFileSync(builtPage, "utf8");
  const blocks = source.match(clearDataBlock) ?? [];
  if (blocks.length !== 1) {
    throw new Error(
      `Expected one Clear Data button in ${builtPage}, found ${blocks.length}`,
    );
  }
  fs.writeFileSync(builtPage, source.replace(clearDataBlock, "!1&&$&"));
}
