import sys
import zs_tests.classes_tests as ct
# import zs_tests.events_test as et
# import zs_tests.graphics_tests as gt
# import zs_tests.entities_tests as ent
# import zs_tests.style_tests as st
# import zs_tests.game_tests as gamt
# import zs_tests.controller_tests as cont

sys.stdout = open("output.txt", "w")
ct.do_tests()
# et.do_tests()
# gt.do_tests()
# ent.do_tests()
# st.do_tests()
# gamt.do_tests()
# cont.do_tests()

# sys.stdout.close()
