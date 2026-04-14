# vhs tape file — generates demo.gif
# Install: brew install vhs   (or scoop install vhs on Windows)
# Render: vhs demo/demo.tape

Output demo/demo.gif

Set FontSize 14
Set Width 1100
Set Height 700
Set Theme "Catppuccin Mocha"
Set Padding 18
Set TypingSpeed 35ms

Type "# CodeLens — semantic PR review demo" Sleep 600ms Enter
Type "# Scenario: 'cache invalidation fix' that quietly added a TTL and broke delete_user" Sleep 800ms Enter
Sleep 600ms

Type "cat demo/scenarios/cache_invalidation/PR_BODY.md" Enter
Sleep 2500ms

Type "clear" Enter
Sleep 300ms

Type "./demo/run_demo.sh" Enter
Sleep 5000ms

Type "# ↑ CodeLens caught: missing test, undocumented TTL, broken delete_user" Sleep 1500ms Enter
Sleep 2000ms
