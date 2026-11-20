# Static design checks

The Fable review exercised alternate source forms. The implementation resolves first font families through custom properties, shorthand and JSX, takes primary families instead of fallbacks, recognizes gradient hues, and finds generic promotional phrases in visible UI copy. Its fixtures include the baseline Trackr page. An imported but unused font does not count. Geometry, navigation usability, active fonts, and computed motion are measured separately in browser captures.

The baseline source measurement used the same checker hash before candidate generation. Raw Fable probes record the findings that motivated these fixes.
