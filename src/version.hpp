#define PICMOVER_MAJOR 0
#define PICMOVER_MINOR 1
#define PICMOVER_PATCH 0

// From https://github.com/dreamworksanimation/openvdb/blob/master/openvdb/version.h
#define PICMOVER_STRINGIFY_(x) #x
#define PICMOVER_STRINGIFY(x) PICMOVER_STRINGIFY_(x)
#define PICMOVER_CONCAT_(x,y) x ## y
#define PICMOVER_CONCAT(x,y) PICMOVER_CONCAT_(x,y)

#define PICMOVER_VERSION_STR                    \
  PICMOVER_CONCAT(v,                            \
  PICMOVER_CONCAT( PICMOVER_MAJOR,              \
  PICMOVER_CONCAT( _, PICMOVER_MINOR )))
