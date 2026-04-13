cmake_minimum_required(VERSION 3.8)
project(bob_central)

find_package(ament_cmake REQUIRED)

ament_python_install_package(${PROJECT_NAME}
  SETUP_CFG
    ${PROJECT_NAME}/setup.cfg
  SCRIPTS_DESTINATION
    lib/${PROJECT_NAME}
)

# Install data files
install(
  DIRECTORY launch prompts config skills
  DESTINATION share/${PROJECT_NAME}
)

# Install meta-data
install(
  FILES package.xml
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_cmake_copyright REQUIRED)
  find_package(ament_cmake_flake8 REQUIRED)
  find_package(ament_cmake_pep257 REQUIRED)
  find_package(ament_cmake_xmllint REQUIRED)
  ament_copyright()
  ament_flake8()
  ament_pep257()
  ament_xmllint()
endif()

ament_package()
