# Complete Fix Plan

## Issues to Fix:
1. Button text not visible
2. Buttons not same size
3. Progress bar not showing percentage properly
4. Info icons not white
5. Tooltips need better descriptions
6. VLANs 300 & 400 not detected

## Root Causes Identified:

### Button Text Issue:
- JavaScript `innerHTML` is overwriting the button content
- Need to ensure white color is set AFTER the DOM is updated
- The `!important` isn't working because it's being overridden

### VLAN Detection Issue:
- Passive listener timeout may not be long enough
- Packet threshold may be too high
- VLANs 300/400 may have very low traffic

## New Approach:
1. Use inline styles in JavaScript when creating button HTML
2. Increase passive listening to 60 seconds
3. Reduce packet threshold to 1
4. Add specific range scanning for VLANs 300-400
5. Fix progress bar to count ALL scanned VLANs (not just responses)
