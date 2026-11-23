"""Geometry fragment for comparing two eligible choices before supporting material."""

from textwrap import dedent


CHOICE_LAYOUT = {
    "use": (
        "Put this fragment first in main. Keep its selectors, fill the factual slots, bind both buttons "
        "and style it for the brief. Put supporting material after it. Verify both actions at scroll zero "
        "at 320 and 390 px."
    ),
    "html": dedent("""\
        <section class="dm-choice" aria-labelledby="dm-title">
          <h1 id="dm-title">[task]</h1>
          <p data-limits>[two limits, with units]</p>
          <article data-option="first">
            <div data-evidence><strong>[first option]</strong><p>[its two values]</p></div>
            <button type="button">Choose [first option] at [time]</button>
          </article>
          <article data-option="second">
            <div data-evidence><strong>[second option]</strong><p>[its two values]</p></div>
            <button type="button">Choose [second option] at [time]</button>
          </article>
          <p data-result role="status" tabindex="-1"></p>
        </section>"""),
    "css": dedent("""\
        .dm-choice { display: grid; gap: 8px; }
        .dm-choice :is(h1,p) { margin: 0; }
        .dm-choice h1 { font-size: clamp(1.625rem,4vw,2.75rem); line-height: 1.04; }
        .dm-choice [data-option] {
          display: grid; grid-template-columns: minmax(0,1fr) minmax(0,1fr);
          align-items: center; gap: 8px; padding-block: 6px;
        }
        .dm-choice button { min-inline-size: 44px; min-block-size: 44px; overflow-wrap: anywhere; }
        .dm-choice button:focus-visible { outline: 2px solid currentColor; outline-offset: 2px; }"""),
}
