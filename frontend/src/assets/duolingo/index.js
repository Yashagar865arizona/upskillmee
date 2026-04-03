// Webpack way
function importAll(r) {
  let icons = {};
  r.keys().forEach((key) => {
    icons[key.replace("./", "")] = r(key);
  });
  return icons;
}

const duolingoIcons = importAll(
  require.context("./", false, /\.svg$/) // (path, recursive, regex)
);

export default duolingoIcons;
