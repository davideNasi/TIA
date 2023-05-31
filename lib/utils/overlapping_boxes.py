def do_rects_collide(a, b):
    return not ((a["top"] + a["height"]) < b["top"] or
                a["top"] > (b["top"] + b["height"]) or
                (a["left"] + a["width"]) < b["left"] or
                a["left"] > (b["left"] + b["width"]))


def find_collisions(rectangles):
    collisions = []

    for rectangle in rectangles:
        collisions_indexes = []

        index = 0
        for current_collision in collisions:
            for rect in current_collision:
                if do_rects_collide(rect, rectangle):
                    collisions_indexes.append(index)
                    break
            index += 1

        if len(collisions_indexes) == 0:
            # This rectangle collides with none and should be appended to collisions array
            collisions.append([rectangle])
        elif len(collisions_indexes) >= 1:
            # There is just one collision, we can merge the same
            collisions[collisions_indexes[0]].append(rectangle)

            # Now we have got multiple collisions, so we need to merge all the collisions with the first one
            # and remove the collision ones
            for i in range(1, len(collisions_indexes)):
                new_index = collisions_indexes[i] - (i - 1)
                # Extend the first colliding array with the new collision match
                collisions[collisions_indexes[0]].extend(collisions[new_index])

                # Remove the element from our collision since it is merged with some other
                collisions.pop(new_index)

    return collisions

def find_non_overlapping_boxes(rectangles):
    collisions = find_collisions(rectangles)
    new_rect = []
    for collision in collisions:
        print(collision)
    return  new_rect


rectangles = [
    {"left": 74, "top": 66.89999389648438, "width": 80.5, "height": 71},
    {"left": 111.5, "top": 95.89999389648438, "width": 125, "height": 84},
    {"left": 177, "top": 120.89999389648438, "width": 168.5, "height": 90},
    {"left": 93, "top": 258.8999938964844, "width": 81.5, "height": 81},
    {"left": 265.5, "top": 320.8999938964844, "width": 92, "height": 83},
    {"left": 393, "top": 210.89999389648438, "width": 88.5, "height": 95}
]

import matplotlib.pyplot as plt
rectangle = rectangles[0]
fig = plt.figure(figsize=[100, 100])
ax = fig.add_subplot(121)
ax.add_patch(plt.Rectangle((rectangle["left"], rectangle["top"]),  rectangle["width"],  rectangle["height"], ls="--", ec="c", fc="none",
                           transform=ax.transAxes))
plt.show()