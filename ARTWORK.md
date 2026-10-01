# Profile artwork

The profile uses a shared navy palette: background `#10263F`, borders `#2B4663`, text `#F3F6FB`, secondary text `#B5C6DC` and blue accents `#8CB9E8`.

The hero, project banners and technology panel are generated with:

```sh
python3 .github/scripts/build_static.py
```

To rebuild only the project banners:

```sh
python3 .github/scripts/build_banners.py
```

Both scripts require `fonttools==4.63.0`. They outline text using the vendored [Geist font](https://github.com/vercel/geist-font), licensed under the [SIL Open Font License](.github/fonts/OFL.txt). Images have descriptive titles and dedicated mobile versions; the README provides matching alternative text.

The activity panel is refreshed weekly by `.github/workflows/refresh-profile.yml`. `refresh_metrics.py --render-existing` rebuilds its artwork from the saved snapshot without making API requests. Project and language totals exclude private, forked, archived and empty repositories, and the profile repository. Commit and pull request searches cover public repositories, including repositories owned by others. Language shares count repositories by their primary language, not lines of code.

Product screenshots use demo or local builds and are labelled in the README. Earlier raster project banners remain in `assets` as historical artwork; the profile now uses the generated SVG versions.
